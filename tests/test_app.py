"""Testes da história #21: servidor FastAPI com rota de upload de PDF.

O endpoint recebe o PDF arrastado, salva em local temporário e dispara
o pipeline (mockado aqui — cada etapa já tem sua própria suíte).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from library_ebooks.app import app
from library_ebooks.pipeline import ConversionResult, PipelineStepError


@pytest.fixture
def client():
    return TestClient(app)


def test_upload_pdf_triggers_pipeline_and_returns_result(monkeypatch, client, tmp_path):
    calls = []

    def _fake_convert_book(pdf_path, **kwargs):
        calls.append((Path(pdf_path).name, kwargs))
        # o PDF enviado deve existir num arquivo temporário até esse ponto
        assert Path(pdf_path).exists()
        epub_path = tmp_path / "livro.epub"
        epub_path.write_text("epub final")
        return ConversionResult(epub_path=epub_path, azw3_path=None)

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    response = client.post(
        "/convert",
        files={"file": ("livro.pdf", "%PDF-1.4 conteúdo fake".encode(), "application/pdf")},
        data={"book_lang": "pt"},
    )

    assert response.status_code == 200
    assert response.json() == {"epub": "livro.epub", "azw3": None}
    assert calls == [("livro.pdf", {"book_lang": "pt", "translate_to": None, "generate_azw3": False})]


def test_rejects_non_pdf_upload(monkeypatch, client):
    def _fail(*args, **kwargs):
        raise AssertionError("não deveria chamar o pipeline para arquivo não-PDF")

    monkeypatch.setattr("library_ebooks.app.convert_book", _fail)

    response = client.post(
        "/convert",
        files={"file": ("livro.txt", b"nao e pdf", "text/plain")},
    )

    assert response.status_code == 400


def test_returns_422_when_pipeline_step_fails(monkeypatch, client):
    def _fail(pdf_path, **kwargs):
        raise PipelineStepError("pdf_to_epub", RuntimeError("calibre não encontrado"))

    monkeypatch.setattr("library_ebooks.app.convert_book", _fail)

    response = client.post(
        "/convert",
        files={"file": ("livro.pdf", "%PDF-1.4 conteúdo fake".encode(), "application/pdf")},
    )

    assert response.status_code == 422
    assert "pdf_to_epub" in response.json()["detail"]


def test_returns_400_when_pipeline_rejects_input(monkeypatch, client):
    def _fail(pdf_path, **kwargs):
        raise ValueError("book_lang é obrigatório quando translate_to é usado")

    monkeypatch.setattr("library_ebooks.app.convert_book", _fail)

    response = client.post(
        "/convert",
        files={"file": ("livro.pdf", "%PDF-1.4 conteúdo fake".encode(), "application/pdf")},
        data={"translate_to": "es"},
    )

    assert response.status_code == 400


# Testes da história #22: frontend com área de drag-and-drop.


def test_index_page_serves_html_with_dropzone(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert 'id="dropzone"' in body
    assert 'accept=".pdf"' in body
    assert "app.js" in body


def test_static_js_is_served_and_wires_drag_and_drop_events(client):
    response = client.get("/app.js")

    assert response.status_code == 200
    body = response.text
    assert "dragover" in body
    assert "drop" in body
    assert "dropzone" in body


# Testes da história #23: seleção de idioma de tradução e formatos de
# saída na UI.


def test_index_page_has_language_and_format_controls(client):
    body = client.get("/").text

    assert 'id="book-lang"' in body
    assert 'id="translate-to"' in body
    for lang in ("pt", "es", "en"):
        assert f'value="{lang}"' in body
    assert 'id="generate-azw3"' in body
    assert 'type="checkbox"' in body
    assert 'id="convert-button"' in body
    assert 'id="result"' in body


def test_app_js_submits_selected_options_to_convert_endpoint(client):
    body = client.get("/app.js").text

    assert "/convert" in body
    assert "FormData" in body
    assert "book-lang" in body
    assert "translate-to" in body
    assert "generate-azw3" in body


def test_temp_pdf_is_removed_after_request(monkeypatch, client):
    captured_path = {}

    def _fake_convert_book(pdf_path, **kwargs):
        captured_path["path"] = Path(pdf_path)
        raise PipelineStepError("pdf_to_epub", RuntimeError("boom"))

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    client.post(
        "/convert",
        files={"file": ("livro.pdf", "%PDF-1.4 conteúdo fake".encode(), "application/pdf")},
    )

    assert not captured_path["path"].exists()
