"""Testes das histórias #14 (gerenciar pacotes de idioma) e #16 (fallback
de pivô de idioma, ex: pt->en->es).
"""

from types import SimpleNamespace

import pytest

from library_ebooks.translate import (
    TranslationPackageError,
    ensure_package_installed,
    translate_text,
)


def _fake_package(from_code, to_code):
    return SimpleNamespace(from_code=from_code, to_code=to_code)


def test_does_nothing_when_package_already_installed(monkeypatch):
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.get_installed_packages",
        lambda: [_fake_package("en", "es")],
    )

    def _fail(*args, **kwargs):
        raise AssertionError("não deveria tentar baixar um pacote já instalado")

    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.update_package_index", _fail
    )
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.install_package_for_language_pair",
        _fail,
    )

    ensure_package_installed("en", "es")  # não deve levantar nem chamar download


def test_downloads_and_installs_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.get_installed_packages", lambda: []
    )
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.update_package_index",
        lambda: calls.append("update_package_index"),
    )

    def _install(from_code, to_code):
        calls.append(("install", from_code, to_code))
        return True

    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.install_package_for_language_pair",
        _install,
    )

    ensure_package_installed("pt", "en")

    assert calls == ["update_package_index", ("install", "pt", "en")]


def test_raises_when_pair_unavailable(monkeypatch):
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.get_installed_packages", lambda: []
    )
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.update_package_index", lambda: None
    )
    monkeypatch.setattr(
        "library_ebooks.translate.argos_package.install_package_for_language_pair",
        lambda from_code, to_code: False,
    )

    with pytest.raises(TranslationPackageError, match="pt.*es"):
        ensure_package_installed("pt", "es")


# Testes da história #16: fallback de pivô de idioma (pt->en->es).


def _available_pairs(pairs):
    """Simula ensure_package_installed: ok pra pares em `pairs`, levanta
    TranslationPackageError pros demais."""

    def _ensure(from_code, to_code):
        if (from_code, to_code) not in pairs:
            raise TranslationPackageError(
                f"sem pacote direto de {from_code!r} para {to_code!r}"
            )

    return _ensure


def test_translates_directly_when_direct_pair_available(monkeypatch):
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed",
        _available_pairs({("en", "es")}),
    )
    monkeypatch.setattr(
        "library_ebooks.translate.argos_translate.translate",
        lambda text, from_code, to_code: f"[{from_code}-{to_code}] {text}",
    )

    assert translate_text("hello", "en", "es") == "[en-es] hello"


def test_falls_back_to_pivot_when_direct_pair_missing(monkeypatch):
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed",
        _available_pairs({("pt", "en"), ("en", "es")}),
    )

    calls = []

    def _translate(text, from_code, to_code):
        calls.append((text, from_code, to_code))
        return f"[{from_code}-{to_code}] {text}"

    monkeypatch.setattr("library_ebooks.translate.argos_translate.translate", _translate)

    result = translate_text("olá", "pt", "es")

    assert result == "[en-es] [pt-en] olá"
    assert calls == [("olá", "pt", "en"), ("[pt-en] olá", "en", "es")]


def test_raises_when_neither_direct_nor_pivot_pair_available(monkeypatch):
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed",
        _available_pairs(set()),  # nenhum par disponível
    )

    with pytest.raises(TranslationPackageError):
        translate_text("olá", "pt", "es")


def test_does_not_pivot_when_pivot_language_is_an_endpoint(monkeypatch):
    # Se o par direto pt->en falha, tentar pivotar por "en" não faz
    # sentido (um dos lados já é o pivô) — o erro original deve subir.
    monkeypatch.setattr(
        "library_ebooks.translate.ensure_package_installed",
        _available_pairs(set()),
    )

    with pytest.raises(TranslationPackageError, match="pt.*en"):
        translate_text("olá", "pt", "en")
