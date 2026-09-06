"""Testes das histórias #10 (localizar o ebook-convert) e #11 (wrapper
PDF -> EPUB).
"""

import subprocess
from pathlib import Path

import pytest

from library_ebooks.convert import (
    CalibreNotFoundError,
    ConversionError,
    convert_pdf_to_epub,
    find_ebook_convert,
)


def test_finds_ebook_convert_in_path(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/local/bin/ebook-convert"
    )
    assert find_ebook_convert() == "/usr/local/bin/ebook-convert"


def test_falls_back_to_macos_bundle_path_when_not_in_path(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(Path, "is_file", lambda self: True)

    result = find_ebook_convert()

    assert result == "/Applications/calibre.app/Contents/MacOS/ebook-convert"


def test_raises_clear_error_when_not_found_anywhere(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    with pytest.raises(CalibreNotFoundError, match="Calibre"):
        find_ebook_convert()


# Testes da história #11: wrapper PDF -> EPUB.


def test_calls_ebook_convert_with_pdf_and_epub_paths(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "library_ebooks.convert.find_ebook_convert",
        lambda: "/opt/calibre/ebook-convert",
    )
    monkeypatch.setattr(
        "library_ebooks.convert.subprocess.run",
        lambda args, **kwargs: calls.append((args, kwargs)),
    )

    pdf_path = tmp_path / "livro.pdf"
    epub_path = tmp_path / "livro.epub"

    result = convert_pdf_to_epub(pdf_path, epub_path)

    assert result == epub_path
    [(args, kwargs)] = calls
    assert args == ["/opt/calibre/ebook-convert", str(pdf_path), str(epub_path)]
    assert kwargs["check"] is True
    assert kwargs["capture_output"] is True


def test_raises_conversion_error_when_calibre_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "library_ebooks.convert.find_ebook_convert",
        lambda: "/opt/calibre/ebook-convert",
    )

    def _fail(args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd=args, stderr=b"arquivo pdf corrompido"
        )

    monkeypatch.setattr("library_ebooks.convert.subprocess.run", _fail)

    with pytest.raises(ConversionError, match="arquivo pdf corrompido"):
        convert_pdf_to_epub(tmp_path / "livro.pdf", tmp_path / "livro.epub")


def test_propagates_calibre_not_found_error(monkeypatch, tmp_path):
    def _raise():
        raise CalibreNotFoundError("ebook-convert não encontrado")

    monkeypatch.setattr("library_ebooks.convert.find_ebook_convert", _raise)

    with pytest.raises(CalibreNotFoundError):
        convert_pdf_to_epub(tmp_path / "livro.pdf", tmp_path / "livro.epub")
