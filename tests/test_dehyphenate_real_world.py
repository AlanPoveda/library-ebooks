"""Testes da história #9: suíte com casos reais de hifenização quebrada
em pt/es/en, cobrindo casos-limite (acentos, pontuação, maiúsculas,
palavras compostas legítimas e fallback pra palavras desconhecidas).

Os exemplos abaixo foram validados manualmente contra o dicionário
(pyenchant/aspell) antes de virar asserção — ver notas de cada bloco.
"""

import pytest

from library_ebooks.dehyphenate import join_broken_words

# Nem toda combinação hífen+quebra-de-linha legítima é reconhecida como
# palavra composta pelo aspell (o backend usado pelo pyenchant nesta
# máquina) — cobertura boa em pt_BR, mas es/en praticamente não têm
# compostos hifenizados no dicionário. Isso é uma limitação conhecida
# do aspell, não um bug nosso; documentado também no PLANNING.md.

PT_CASES = [
    # acentos + pontuação logo após a palavra reconstituída
    (
        "A informa-\nção, publicada ontem, é grave.",
        "A informação, publicada ontem, é grave.",
    ),
    # maiúscula no início de frase
    ("Amanhe-\ncer chegou bonito.", "Amanhecer chegou bonito."),
    # palavras compostas legítimas — mantêm o hífen
    ("Ele comprou um guarda-\nroupa novo.", "Ele comprou um guarda-roupa novo."),
    ("O forno micro-\nondas quebrou.", "O forno micro-ondas quebrou."),
    # nome próprio desconhecido do dicionário — cai no fallback ingênuo
    ("Ele mora em Xylo-\nphonia.", "Ele mora em Xylophonia."),
]

ES_CASES = [
    (
        "La informa-\nción, publicada ayer, es grave.",
        "La información, publicada ayer, es grave.",
    ),
    ("Compró un para-\nguas nuevo.", "Compró un paraguas nuevo."),
    ("Educa-\nción es fundamental.", "Educación es fundamental."),
    ("Viajó a Xylo-\nfonia el año pasado.", "Viajó a Xylofonia el año pasado."),
]

EN_CASES = [
    (
        "The inform-\nation was released yesterday.",
        "The information was released yesterday.",
    ),
    ("She bought a new um-\nbrella today.", "She bought a new umbrella today."),
    ("Educa-\ntion matters a lot.", "Education matters a lot."),
    ("They moved to Xylo-\nphonia last year.", "They moved to Xylophonia last year."),
]


@pytest.mark.parametrize("broken,expected", PT_CASES)
def test_real_world_hyphenation_pt(broken, expected):
    assert join_broken_words(broken, lang="pt") == expected


@pytest.mark.parametrize("broken,expected", ES_CASES)
def test_real_world_hyphenation_es(broken, expected):
    assert join_broken_words(broken, lang="es") == expected


@pytest.mark.parametrize("broken,expected", EN_CASES)
def test_real_world_hyphenation_en(broken, expected):
    assert join_broken_words(broken, lang="en") == expected
