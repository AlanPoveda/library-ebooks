"""Testes da história #27: rodar LanguageTool local e listar problemas
de um texto (posição, regra, mensagem, sugestões), para pt/es/en.

Os testes mockam language_tool_python.LanguageTool — subir o servidor
LanguageTool de verdade é pesado (baixa ~200MB na primeira vez, sobe
uma JVM) e não é isso que estamos testando aqui.
"""

from types import SimpleNamespace

import pytest

from library_ebooks.lint import GrammarIssue, check_text


def _fake_match(offset, length, message, rule_id, replacements):
    return SimpleNamespace(
        offset=offset,
        error_length=length,
        message=message,
        rule_id=rule_id,
        replacements=replacements,
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
        _fake_match(0, 4, "Erro de concordância", "PT_CONCORDANCIA", ["Isto"]),
        _fake_match(10, 3, "Palavra desconhecida", "PT_SPELLING", ["dia", "dias"]),
    ]
    fake_tool = _FakeLanguageTool("pt-BR", matches)
    monkeypatch.setattr(
        "library_ebooks.lint.language_tool_python.LanguageTool",
        lambda lang_code: fake_tool,
    )

    issues = check_text("Isso e um teste bom dia.", lang="pt")

    assert issues == [
        GrammarIssue(0, 4, "Erro de concordância", "PT_CONCORDANCIA", ["Isto"]),
        GrammarIssue(10, 3, "Palavra desconhecida", "PT_SPELLING", ["dia", "dias"]),
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
