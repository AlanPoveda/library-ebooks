"""Testes da história #27: rodar LanguageTool local e listar problemas
de um texto (posição, regra, mensagem, sugestões), para pt/es/en.

Os testes mockam language_tool_python.LanguageTool — subir o servidor
LanguageTool de verdade é pesado (baixa ~200MB na primeira vez, sobe
uma JVM) e não é isso que estamos testando aqui.
"""

from types import SimpleNamespace

import pytest

from library_ebooks.lint import GrammarIssue, apply_high_confidence_corrections, check_text


def _fake_match(offset, length, message, rule_id, replacements, issue_type="misspelling"):
    return SimpleNamespace(
        offset=offset,
        error_length=length,
        message=message,
        rule_id=rule_id,
        replacements=replacements,
        rule_issue_type=issue_type,
    )


class _FakeLanguageTool:
    def __init__(self, lang_code, matches):
        self.lang_code = lang_code
        self._matches = matches
        self.closed = False

    def check(self, text):
        return self._matches

    def close(self):
        self.closed = True


def test_check_text_returns_issues_with_position_rule_message_suggestions(monkeypatch):
    matches = [
        _fake_match(0, 4, "Erro de concordância", "PT_CONCORDANCIA", ["Isto"], "grammar"),
        _fake_match(10, 3, "Palavra desconhecida", "PT_SPELLING", ["dia", "dias"]),
    ]
    fake_tool = _FakeLanguageTool("pt-BR", matches)
    monkeypatch.setattr(
        "library_ebooks.lint.language_tool_python.LanguageTool",
        lambda lang_code: fake_tool,
    )

    issues = check_text("Isso e um teste bom dia.", lang="pt")

    assert issues == [
        GrammarIssue(0, 4, "Erro de concordância", "PT_CONCORDANCIA", ["Isto"], "grammar"),
        GrammarIssue(10, 3, "Palavra desconhecida", "PT_SPELLING", ["dia", "dias"], "misspelling"),
    ]
    assert fake_tool.closed  # não deve vazar o processo/servidor do LanguageTool


def test_check_text_returns_empty_list_when_no_issues(monkeypatch):
    fake_tool = _FakeLanguageTool("en-US", [])
    monkeypatch.setattr(
        "library_ebooks.lint.language_tool_python.LanguageTool",
        lambda lang_code: fake_tool,
    )

    assert check_text("This is fine.", lang="en") == []


@pytest.mark.parametrize(
    "lang,expected_code", [("pt", "pt-BR"), ("es", "es"), ("en", "en-US")]
)
def test_check_text_uses_correct_language_tool_code(monkeypatch, lang, expected_code):
    captured = {}

    def _fake_constructor(lang_code):
        captured["lang_code"] = lang_code
        return _FakeLanguageTool(lang_code, [])

    monkeypatch.setattr(
        "library_ebooks.lint.language_tool_python.LanguageTool", _fake_constructor
    )

    check_text("texto qualquer", lang=lang)

    assert captured["lang_code"] == expected_code


def test_check_text_raises_for_unsupported_language():
    with pytest.raises(ValueError, match="fr"):
        check_text("texte", lang="fr")


# Testes da história #28: aplicar automaticamente correções de alta
# confiança (uma única sugestão, regra que não é de estilo); o resto
# fica só no relatório, sem alterar o texto.


def test_applies_unambiguous_spelling_correction():
    text = "Isso e um teste."
    issue = GrammarIssue(5, 1, "Erro", "PT_E_VERBO", ["é"], "misspelling")

    corrected, remaining = apply_high_confidence_corrections(text, [issue])

    assert corrected == "Isso é um teste."
    assert remaining == []


def test_applies_misspelling_using_top_suggestion_even_with_multiple_candidates():
    # Achado real testando contra o LanguageTool de verdade: pra erros de
    # ortografia (misspelling), o corretor quase sempre devolve várias
    # sugestões rankeadas (ex.: "concordancia" -> concordância/concordança/
    # concordâncias/concordanças) mesmo quando o erro é óbvio e a primeira
    # sugestão é claramente a certa. Exigir sugestão única deixaria essa
    # categoria inteira sem correção automática — então "misspelling" usa
    # a primeira sugestão mesmo havendo mais de uma.
    text = "Erro de concordancia aqui."
    issue = GrammarIssue(
        8, 12, "Erro ortográfico", "MORFOLOGIK_RULE_PT_BR",
        ["concordância", "concordança", "concordâncias"], "misspelling",
    )

    corrected, remaining = apply_high_confidence_corrections(text, [issue])

    assert corrected == "Erro de concordância aqui."
    assert remaining == []


def test_does_not_auto_apply_style_suggestions():
    text = "O livro foi muito bom."
    issue = GrammarIssue(12, 5, "Considere um sinônimo", "STYLE_RULE", ["ótimo"], "style")

    corrected, remaining = apply_high_confidence_corrections(text, [issue])

    assert corrected == text  # texto não muda
    assert remaining == [issue]


def test_does_not_auto_apply_ambiguous_multiple_replacements():
    text = "Ele viu ela."
    issue = GrammarIssue(8, 3, "Pronome ambíguo", "PRONOUN_RULE", ["a", "ela mesma"], "grammar")

    corrected, remaining = apply_high_confidence_corrections(text, [issue])

    assert corrected == text
    assert remaining == [issue]


def test_applies_multiple_corrections_without_offset_drift():
    text = "Isso e bom, mas aquilo nao e."
    issues = [
        GrammarIssue(5, 1, "Erro", "PT_E_VERBO", ["é"], "misspelling"),
        GrammarIssue(27, 1, "Erro", "PT_E_VERBO", ["é"], "misspelling"),
        GrammarIssue(23, 3, "Erro", "PT_NAO", ["não"], "misspelling"),
    ]

    corrected, remaining = apply_high_confidence_corrections(text, issues)

    assert corrected == "Isso é bom, mas aquilo não é."
    assert remaining == []


def test_returns_remaining_issues_in_original_offset_order():
    text = "a b c"
    ambiguous_1 = GrammarIssue(0, 1, "m1", "R1", ["x", "y"], "grammar")
    ambiguous_2 = GrammarIssue(4, 1, "m2", "R2", ["x", "y"], "grammar")

    _, remaining = apply_high_confidence_corrections(text, [ambiguous_2, ambiguous_1])

    assert remaining == [ambiguous_1, ambiguous_2]
