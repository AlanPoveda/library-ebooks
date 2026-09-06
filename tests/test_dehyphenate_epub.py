"""Testes da história #8: aplicar dehyphenation em conteúdo HTML de EPUB,
preservando tags e formatação ao redor do texto.
"""

from ebooklib import ITEM_DOCUMENT, epub

from library_ebooks.dehyphenate import dehyphenate_epub


def _build_epub(tmp_path, content: str, file_name: str = "chap1.xhtml"):
    book = epub.EpubBook()
    book.set_identifier("id123")
    book.set_title("Livro de teste")
    book.set_language("pt")

    chapter = epub.EpubHtml(title="Cap 1", file_name=file_name, lang="pt")
    chapter.content = content
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc = (chapter,)
    book.spine = ["nav", chapter]

    input_path = tmp_path / "entrada.epub"
    epub.write_epub(str(input_path), book)
    return input_path


def _read_chapter_content(epub_path, file_name: str = "chap1.xhtml") -> str:
    book = epub.read_epub(str(epub_path))
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        if item.file_name == file_name:
            return item.get_content().decode("utf-8")
    raise AssertionError(f"capítulo {file_name} não encontrado no EPUB de saída")


def test_joins_broken_word_inside_epub_paragraph(tmp_path):
    input_path = _build_epub(
        tmp_path,
        "<html><body><p>A informa-\nção chegou.</p></body></html>",
    )
    output_path = tmp_path / "saida.epub"

    result = dehyphenate_epub(input_path, output_path)

    assert result == output_path
    assert "informação" in _read_chapter_content(output_path)
    assert "informa-" not in _read_chapter_content(output_path)


def test_preserves_surrounding_tags_and_formatting(tmp_path):
    input_path = _build_epub(
        tmp_path,
        "<html><body><p>A informa-\nção chegou. <b>Ótimo</b> resultado.</p></body></html>",
    )
    output_path = tmp_path / "saida.epub"

    dehyphenate_epub(input_path, output_path)

    content = _read_chapter_content(output_path)
    assert "informação" in content
    assert "<b>Ótimo</b>" in content


def test_dehyphenate_epub_uses_dictionary_validation_when_lang_given(tmp_path):
    input_path = _build_epub(
        tmp_path,
        "<html><body><p>Precisei do guarda-\nchuva hoje.</p></body></html>",
    )
    output_path = tmp_path / "saida.epub"

    dehyphenate_epub(input_path, output_path, lang="pt")

    assert "guarda-chuva" in _read_chapter_content(output_path)
