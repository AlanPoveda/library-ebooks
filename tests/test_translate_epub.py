"""Testes das histórias #15 (traduzir texto preservando estrutura
HTML/parágrafos) e #17 (validar idioma de destino suportado antes de
traduzir).
"""

import pytest

from library_ebooks.translate import UnsupportedLanguageError, translate_epub


def _fake_translate(text, from_code, to_code):
    # Sem ">" no marcador: esse caractere seria escapado como "&gt;" pelo
    # BeautifulSoup ao serializar o HTML de volta, o que é o comportamento
    # correto — só evitamos aqui pra manter o assert simples de ler.
    return f"[{from_code}-{to_code}] {text}"


def test_translates_text_nodes_and_ensures_package(
    monkeypatch, build_epub, read_epub_chapter, tmp_path
):
    calls = []
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed",
        lambda from_code, to_code: calls.append((from_code, to_code)),
    )
    monkeypatch.setattr("library_ebooks.translate.argos_translate.translate", _fake_translate)

    input_path = build_epub("<html><body><p>Hello world.</p></body></html>")
    output_path = tmp_path / "saida.epub"

    result = translate_epub(input_path, output_path, "en", "pt")

    assert result == output_path
    content = read_epub_chapter(output_path)
    assert "[en-pt] Hello world." in content
    assert ("en", "pt") in calls


def test_preserves_tags_and_structure(monkeypatch, build_epub, read_epub_chapter, tmp_path):
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed", lambda from_code, to_code: None
    )
    monkeypatch.setattr("library_ebooks.translate.argos_translate.translate", _fake_translate)

    input_path = build_epub(
        "<html><body><p>Hello world. <b>Great</b> news.</p></body></html>"
    )
    output_path = tmp_path / "saida.epub"

    translate_epub(input_path, output_path, "en", "pt")

    content = read_epub_chapter(output_path)
    assert "<b>[en-pt] Great</b>" in content


def test_skips_whitespace_only_nodes(monkeypatch, build_epub, tmp_path):
    calls = []
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed", lambda from_code, to_code: None
    )

    def _record_translate(text, from_code, to_code):
        calls.append(text)
        return text

    monkeypatch.setattr(
        "library_ebooks.translate.argos_translate.translate", _record_translate
    )

    input_path = build_epub(
        "<html><body>\n  <p>Hello.</p>\n  <p>Bye.</p>\n</body></html>"
    )
    output_path = tmp_path / "saida.epub"

    translate_epub(input_path, output_path, "en", "pt")

    assert calls == ["Hello.", "Bye."]


def test_rejects_unsupported_target_language_before_translating(
    monkeypatch, build_epub, tmp_path
):
    def _fail(*args, **kwargs):
        raise AssertionError("não deveria tentar traduzir com idioma inválido")

    monkeypatch.setattr("library_ebooks.translate.ensure_package_installed", _fail)
    monkeypatch.setattr("library_ebooks.translate.argos_translate.translate", _fail)

    input_path = build_epub("<html><body><p>Hello.</p></body></html>")
    output_path = tmp_path / "saida.epub"

    with pytest.raises(UnsupportedLanguageError):
        translate_epub(input_path, output_path, "en", "fr")
