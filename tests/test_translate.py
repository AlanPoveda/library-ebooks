"""Testes da história #14: verificar se os pacotes de idioma do Argos
Translate estão instalados localmente e baixá-los se necessário.
"""

from types import SimpleNamespace

import pytest

from library_ebooks.translate import TranslationPackageError, ensure_package_installed


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
