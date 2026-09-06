"""Utilitário compartilhado para transformar o texto de um EPUB nó a nó,
preservando tags e formatação ao redor (usado pelo dehyphenate e pela
tradução — ver `PLANNING.md`)."""

from pathlib import Path
from typing import Callable

from bs4 import BeautifulSoup, NavigableString
from ebooklib import ITEM_DOCUMENT, epub


def apply_to_epub_text_nodes(
    input_path: str | Path,
    output_path: str | Path,
    transform: Callable[[str], str],
) -> Path:
    """Aplica `transform` a cada nó de texto não-vazio dos documentos HTML
    internos de um EPUB, sem alterar as tags ao redor.

    Nós só com espaço em branco são pulados (não faz sentido "traduzir"
    ou "corrigir" um espaço de indentação entre tags). Nós especiais que
    também são subclasses de `NavigableString` (declaração XML, comentários,
    doctype etc.) são ignorados via `type(node) is NavigableString` — um
    `isinstance` os pegaria por engano e corromperia a estrutura do arquivo.
    """
    book = epub.read_epub(str(input_path))

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        # nav.xhtml é o documento de navegação/TOC do EPUB, não conteúdo
        # do livro — não deve ser corrigido/traduzido junto com os capítulos.
        if item.file_name == "nav.xhtml":
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for node in soup.find_all(string=True):
            if type(node) is not NavigableString or not node.strip():
                continue
            node.replace_with(transform(str(node)))
        item.set_content(str(soup).encode("utf-8"))

    # Workaround para uma limitação do ebooklib: ao ler um EPUB, o TOC vem
    # como objetos `Link` sem `uid`, o que quebra a regeneração do NCX na
    # escrita. Reconstruímos o TOC a partir dos próprios documentos (que
    # têm id válido), achatando qualquer hierarquia de seções que houvesse.
    book.toc = tuple(
        item
        for item in book.get_items_of_type(ITEM_DOCUMENT)
        if item.file_name != "nav.xhtml"
    )

    epub.write_epub(str(output_path), book)
    return Path(output_path)
