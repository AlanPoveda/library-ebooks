"""Correção de hifenização quebrada vinda da extração de PDF.

Quando um PDF com texto justificado é extraído, palavras que caíram no
fim da linha ficam com um hífen seguido de quebra de linha, ex.:
"informa-\\nção". Este módulo reconstitui a palavra original.
"""

import re
from pathlib import Path

import enchant
from bs4 import BeautifulSoup, NavigableString
from ebooklib import ITEM_DOCUMENT, epub

# Hífen imediatamente seguido de quebra de linha, com um "run" de
# caracteres de palavra (letra/dígito/underscore, incluindo acentuados)
# de cada lado — é esse run que forma o fragmento da palavra quebrada.
_BROKEN_WORD_PATTERN = re.compile(r"(\w+)-\n(\w+)", re.UNICODE)

# Códigos de idioma simples usados no resto do app (mesmos do épico de
# tradução: es/en/pt) mapeados para os códigos de dicionário do enchant.
_ENCHANT_LANG_MAP = {"pt": "pt_BR", "es": "es", "en": "en_US"}


def join_broken_words(text: str, lang: str | None = None) -> str:
    """Junta palavras quebradas por hífen no fim de linha.

    Ex.: "informa-\\nção" -> "informação"

    Sem `lang`, apenas junta (comportamento ingênuo da história #6): não
    distingue hífens de quebra de linha de hífens legítimos.

    Com `lang` ("pt", "es" ou "en"), valida contra o dicionário: se a
    palavra juntada for válida, junta; se a versão com hífen for uma
    palavra composta legítima (ex.: "guarda-chuva"), mantém o hífen; se
    nenhuma das duas for reconhecida, cai no comportamento ingênuo.
    """
    if lang is None:
        return _BROKEN_WORD_PATTERN.sub(r"\1\2", text)

    if lang not in _ENCHANT_LANG_MAP:
        raise ValueError(
            f"idioma não suportado: {lang!r} (use um de {sorted(_ENCHANT_LANG_MAP)})"
        )

    dictionary = enchant.Dict(_ENCHANT_LANG_MAP[lang])

    def _resolve(match: re.Match[str]) -> str:
        prefix, suffix = match.group(1), match.group(2)
        joined = prefix + suffix
        hyphenated = f"{prefix}-{suffix}"
        if dictionary.check(joined):
            return joined
        if dictionary.check(hyphenated):
            return hyphenated
        return joined

    return _BROKEN_WORD_PATTERN.sub(_resolve, text)


def dehyphenate_epub(
    input_path: str | Path, output_path: str | Path, lang: str | None = None
) -> Path:
    """Aplica `join_broken_words` a todo o texto de um EPUB.

    Percorre os documentos HTML internos do EPUB e corrige a
    hifenização apenas dentro dos nós de texto, sem tocar nas tags ao
    redor — formatação (negrito, itálico etc.) é preservada.
    """
    book = epub.read_epub(str(input_path))

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for node in soup.find_all(string=True):
            if not isinstance(node, NavigableString):
                continue
            fixed_text = join_broken_words(str(node), lang=lang)
            if fixed_text != str(node):
                node.replace_with(fixed_text)
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
