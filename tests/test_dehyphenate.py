"""Testes da história #6: detectar e juntar palavras quebradas por
hífen no fim de linha.

Validação por dicionário (não juntar hífens legítimos, ex: "guarda-\\nchuva")
fica para a história #7 e não é coberta aqui.
"""

from library_ebooks.dehyphenate import join_broken_words


def test_join_simple_hyphenated_word():
    assert join_broken_words("informa-\nção") == "informação"


def test_join_word_broken_across_multiple_lines_of_paragraph():
    text = "O relató-\nrio foi entregue ontem."
    assert join_broken_words(text) == "O relatório foi entregue ontem."


def test_does_not_touch_hyphen_in_middle_of_line():
    text = "Isso é bom-mas-ruim ao mesmo tempo."
    assert join_broken_words(text) == text


def test_does_not_touch_text_without_hyphens():
    text = "Nada para corrigir aqui."
    assert join_broken_words(text) == text


def test_join_preserves_surrounding_whitespace_and_newlines():
    text = "Primeira linha.\nSegunda pala-\nvra continua.\nTerceira linha."
    expected = "Primeira linha.\nSegunda palavra continua.\nTerceira linha."
    assert join_broken_words(text) == expected
