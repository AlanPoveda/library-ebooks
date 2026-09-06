"""Testes da história #10: localizar o binário ebook-convert do Calibre,
tanto no PATH quanto no caminho padrão do bundle do calibre.app no macOS.
"""

from pathlib import Path

import pytest

from library_ebooks.convert import CalibreNotFoundError, find_ebook_convert


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
