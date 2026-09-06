import pytest
from ebooklib import ITEM_DOCUMENT, epub


@pytest.fixture
def build_epub(tmp_path):
    """Constrói um EPUB mínimo com um único capítulo, para testes."""

    def _build(content: str, file_name: str = "chap1.xhtml"):
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

    return _build


@pytest.fixture
def read_epub_chapter():
    """Lê de volta o conteúdo HTML de um capítulo de um EPUB gerado."""

    def _read(epub_path, file_name: str = "chap1.xhtml") -> str:
        book = epub.read_epub(str(epub_path))
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            if item.file_name == file_name:
                return item.get_content().decode("utf-8")
        raise AssertionError(f"capítulo {file_name} não encontrado no EPUB de saída")

    return _read
