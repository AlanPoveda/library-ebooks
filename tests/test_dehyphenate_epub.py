"""Testes da história #8: aplicar dehyphenation em conteúdo HTML de EPUB,
preservando tags e formatação ao redor do texto.
"""

from library_ebooks.dehyphenate import dehyphenate_epub


def test_joins_broken_word_inside_epub_paragraph(build_epub, read_epub_chapter, tmp_path):
    input_path = build_epub("<html><body><p>A informa-\nção chegou.</p></body></html>")
    output_path = tmp_path / "saida.epub"

    result = dehyphenate_epub(input_path, output_path)

    assert result == output_path
    content = read_epub_chapter(output_path)
    assert "informação" in content
    assert "informa-" not in content


def test_preserves_surrounding_tags_and_formatting(build_epub, read_epub_chapter, tmp_path):
    input_path = build_epub(
        "<html><body><p>A informa-\nção chegou. <b>Ótimo</b> resultado.</p></body></html>"
    )
    output_path = tmp_path / "saida.epub"

    dehyphenate_epub(input_path, output_path)

    content = read_epub_chapter(output_path)
    assert "informação" in content
    assert "<b>Ótimo</b>" in content


def test_dehyphenate_epub_uses_dictionary_validation_when_lang_given(
    build_epub, read_epub_chapter, tmp_path
):
    input_path = build_epub("<html><body><p>Precisei do guarda-\nchuva hoje.</p></body></html>")
    output_path = tmp_path / "saida.epub"

    dehyphenate_epub(input_path, output_path, lang="pt")

    assert "guarda-chuva" in read_epub_chapter(output_path)
