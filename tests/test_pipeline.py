"""Testes da história #18: orquestrar o pipeline completo — PDF -> EPUB
(Calibre) -> dehyphenate -> tradução opcional -> AZW3 opcional (Calibre).

Cada etapa já tem sua própria suíte de testes (test_convert.py,
test_dehyphenate*.py, test_translate*.py); aqui só verificamos que o
pipeline encadeia as chamadas certas, na ordem certa, com os caminhos
certos — todas as etapas são mockadas.
"""

import logging

import pytest

from library_ebooks.pipeline import PipelineStepError, convert_book


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


# Testes da história #19: gerenciamento de arquivos temporários e pasta books/.


def test_uses_books_dir_by_default_when_output_dir_not_given(mocked_steps, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, book_lang="pt")

    assert result.epub_path.resolve() == tmp_path / "books" / "livro.epub"
    assert result.epub_path.exists()


def test_removes_untranslated_intermediate_epub_when_translated(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, tmp_path, book_lang="pt", translate_to="es")

    clean_epub_path = tmp_path / "livro.epub"
    assert not clean_epub_path.exists()  # era só intermediário pra chegar na tradução
    assert result.epub_path == tmp_path / "livro.es.epub"
    assert result.epub_path.exists()


def test_keeps_final_epub_when_azw3_is_also_generated(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    result = convert_book(pdf_path, tmp_path, book_lang="pt", generate_azw3=True)

    assert result.epub_path.exists()
    assert result.azw3_path.exists()


# Testes da história #20: tratamento de erros e logging do pipeline.


def test_wraps_pdf_to_epub_failure_identifying_the_step(mocked_steps, monkeypatch, tmp_path):
    original = ValueError("pdf corrompido")

    def _fail(pdf_path, epub_path):
        raise original

    monkeypatch.setattr("library_ebooks.pipeline.convert_pdf_to_epub", _fail)

    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with pytest.raises(PipelineStepError) as exc_info:
        convert_book(pdf_path, tmp_path, book_lang="pt")

    assert exc_info.value.step == "pdf_to_epub"
    assert exc_info.value.__cause__ is original


def test_wraps_dehyphenate_failure_identifying_the_step(mocked_steps, monkeypatch, tmp_path):
    original = RuntimeError("html inválido")

    def _fail(input_path, output_path, lang=None):
        raise original

    monkeypatch.setattr("library_ebooks.pipeline.dehyphenate_epub", _fail)

    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with pytest.raises(PipelineStepError) as exc_info:
        convert_book(pdf_path, tmp_path, book_lang="pt")

    assert exc_info.value.step == "dehyphenate"
    assert exc_info.value.__cause__ is original


def test_wraps_translate_failure_identifying_the_step(mocked_steps, monkeypatch, tmp_path):
    original = RuntimeError("sem pacote de idioma")

    def _fail(input_path, output_path, from_code, to_code):
        raise original

    monkeypatch.setattr("library_ebooks.pipeline.translate_epub", _fail)

    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with pytest.raises(PipelineStepError) as exc_info:
        convert_book(pdf_path, tmp_path, book_lang="pt", translate_to="es")

    assert exc_info.value.step == "translate"
    assert exc_info.value.__cause__ is original


def test_wraps_azw3_failure_identifying_the_step(mocked_steps, monkeypatch, tmp_path):
    original = RuntimeError("calibre falhou")

    def _fail(epub_path, azw3_path):
        raise original

    monkeypatch.setattr("library_ebooks.pipeline.convert_epub_to_azw3", _fail)

    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with pytest.raises(PipelineStepError) as exc_info:
        convert_book(pdf_path, tmp_path, book_lang="pt", generate_azw3=True)

    assert exc_info.value.step == "epub_to_azw3"
    assert exc_info.value.__cause__ is original


def test_logs_progress_for_each_step(mocked_steps, tmp_path, caplog):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with caplog.at_level(logging.INFO, logger="library_ebooks.pipeline"):
        convert_book(pdf_path, tmp_path, book_lang="pt")

    messages = " ".join(caplog.messages)
    assert "pdf_to_epub" in messages or "EPUB" in messages
    assert "dehyphenate" in messages or "hifenização" in messages


def test_logs_error_when_a_step_fails(mocked_steps, monkeypatch, tmp_path, caplog):
    def _fail(pdf_path, epub_path):
        raise RuntimeError("boom")

    monkeypatch.setattr("library_ebooks.pipeline.convert_pdf_to_epub", _fail)

    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    with caplog.at_level(logging.ERROR, logger="library_ebooks.pipeline"):
        with pytest.raises(PipelineStepError):
            convert_book(pdf_path, tmp_path, book_lang="pt")

    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert "pdf_to_epub" in " ".join(caplog.messages)


# Testes da história #25: reportar progresso (qual etapa está rodando) via
# um callback opcional, pra quem chama o pipeline (o app web) poder exibir.


def test_on_progress_is_called_for_each_step_in_default_run(mocked_steps, tmp_path):
    progress = []
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    convert_book(pdf_path, tmp_path, book_lang="pt", on_progress=progress.append)

    assert progress == ["pdf_to_epub", "dehyphenate"]


def test_on_progress_includes_translate_and_azw3_when_requested(mocked_steps, tmp_path):
    progress = []
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    convert_book(
        pdf_path,
        tmp_path,
        book_lang="pt",
        translate_to="es",
        generate_azw3=True,
        on_progress=progress.append,
    )

    assert progress == ["pdf_to_epub", "dehyphenate", "translate", "epub_to_azw3"]


def test_on_progress_is_optional(mocked_steps, tmp_path):
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_text("conteúdo fake do pdf")

    convert_book(pdf_path, tmp_path, book_lang="pt")  # não deve levantar sem on_progress
