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


# Testes da história #7: validação por dicionário (pt_BR / es / en).
# Sem `lang`, o comportamento continua o mesmo dos testes acima (ingênuo).


def test_joins_when_result_is_a_valid_word_pt():
    assert join_broken_words("informa-\nção", lang="pt") == "informação"


def test_keeps_hyphen_for_legitimate_compound_word_pt():
    assert join_broken_words("guarda-\nchuva", lang="pt") == "guarda-chuva"


def test_joins_when_result_is_a_valid_word_es():
    assert join_broken_words("informa-\nción", lang="es") == "información"


def test_joins_when_result_is_a_valid_word_en():
    assert join_broken_words("inform-\nation", lang="en") == "information"


def test_falls_back_to_naive_join_when_word_unknown_in_dictionary():
    # Nem "asdfqwzx" nem "asdf-qwzx" existem em nenhum dicionário — no
    # caso de dúvida, o comportamento seguro é o mesmo da história #6.
    assert join_broken_words("asdf-\nqwzx", lang="pt") == "asdfqwzx"


def test_raises_for_unsupported_language():
    import pytest

    with pytest.raises(ValueError):
        join_broken_words("informa-\nção", lang="fr")
