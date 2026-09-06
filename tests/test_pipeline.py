"""Testes da história #18: orquestrar o pipeline completo — PDF -> EPUB
(Calibre) -> dehyphenate -> tradução opcional -> AZW3 opcional (Calibre).

Cada etapa já tem sua própria suíte de testes (test_convert.py,
test_dehyphenate*.py, test_translate*.py); aqui só verificamos que o
pipeline encadeia as chamadas certas, na ordem certa, com os caminhos
certos — todas as etapas são mockadas.
"""

import pytest

from library_ebooks.pipeline import convert_book


def _write_marker(path, text):
    path.write_text(text)
    return path


@pytest.fixture
def mocked_steps(monkeypatch):
    calls = []

    def _convert_pdf_to_epub(pdf_path, epub_path):
        calls.append(("pdf_to_epub", pdf_path, epub_path))
        return _write_marker(epub_path, "epub bruto")

    def _dehyphenate_epub(input_path, output_path, lang=None):
        calls.append(("dehyphenate", input_path, output_path, lang))
        return _write_marker(output_path, "epub limpo")

    def _translate_epub(input_path, output_path, from_code, to_code):
        calls.append(("translate", input_path, output_path, from_code, to_code))
        return _write_marker(output_path, "epub traduzido")

    def _convert_epub_to_azw3(epub_path, azw3_path):
        calls.append(("epub_to_azw3", epub_path, azw3_path))
        return _write_marker(azw3_path, "azw3")

    monkeypatch.setattr("library_ebooks.pipeline.convert_pdf_to_epub", _convert_pdf_to_epub)
    monkeypatch.setattr("library_ebooks.pipeline.dehyphenate_epub", _dehyphenate_epub)
    monkeypatch.setattr("library_ebooks.pipeline.translate_epub", _translate_epub)
    monkeypatch.setattr("library_ebooks.pipeline.convert_epub_to_azw3", _convert_epub_to_azw3)

    return calls


def test_runs_pdf_to_epub_and_dehyphenate_by_default(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, tmp_path, book_lang="pt")

    steps = [call[0] for call in mocked_steps]
    assert steps == ["pdf_to_epub", "dehyphenate"]
    assert result.epub_path.exists()
    assert result.epub_path.read_text() == "epub limpo"
    assert result.azw3_path is None


def test_removes_intermediate_raw_epub_after_dehyphenate(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    convert_book(pdf_path, tmp_path, book_lang="pt")

    raw_epub_call = next(call for call in mocked_steps if call[0] == "pdf_to_epub")
    raw_epub_path = raw_epub_call[2]
    assert not raw_epub_path.exists()


def test_translates_when_translate_to_given(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, tmp_path, book_lang="pt", translate_to="es")

    steps = [call[0] for call in mocked_steps]
    assert steps == ["pdf_to_epub", "dehyphenate", "translate"]
    translate_call = next(call for call in mocked_steps if call[0] == "translate")
    assert translate_call[3:] == ("pt", "es")
    assert result.epub_path.read_text() == "epub traduzido"


def test_generates_azw3_when_requested(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, tmp_path, book_lang="pt", generate_azw3=True)

    steps = [call[0] for call in mocked_steps]
    assert steps == ["pdf_to_epub", "dehyphenate", "epub_to_azw3"]
    assert result.azw3_path is not None
    assert result.azw3_path.read_text() == "azw3"


def test_azw3_is_generated_from_translated_epub_when_both_requested(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(
        pdf_path, tmp_path, book_lang="pt", translate_to="es", generate_azw3=True
    )

    azw3_call = next(call for call in mocked_steps if call[0] == "epub_to_azw3")
    assert azw3_call[1] == result.epub_path  # convertido a partir do epub final (traduzido)


def test_raises_when_translate_requested_without_book_lang(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with pytest.raises(ValueError, match="book_lang"):
        convert_book(pdf_path, tmp_path, translate_to="es")

    assert mocked_steps == []  # não deve rodar nenhuma etapa
