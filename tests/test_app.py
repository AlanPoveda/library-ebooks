"""Testes das histórias #21-#25 do épico App Web.

#21 upload de PDF, #22 drag-and-drop, #23 seleção de idioma/formato,
#24 download dos arquivos gerados, #25 feedback de progresso (a razão
de /convert virar um job em background + polling em /progress/{id}).
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from library_ebooks.app import app
from library_ebooks.pipeline import ConversionResult, PipelineStepError


@pytest.fixture
def client():
    return TestClient(app)


def _wait_for_done(client, job_id, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/progress/{job_id}").json()
        if data["done"]:
            return data
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} não terminou em {timeout}s")


def _post_pdf(client, **form_data):
    return client.post(
        "/convert",
        files={"file": ("livro.pdf", "%PDF-1.4 conteúdo fake".encode(), "application/pdf")},
        data=form_data,
    )


# Testes das histórias #21 e #25: upload dispara um job em background,
# reportado via GET /progress/{job_id}.


def test_upload_pdf_returns_a_job_id(monkeypatch, client, tmp_path):
    def _fake_convert_book(pdf_path, **kwargs):
        epub_path = tmp_path / "livro.epub"
        epub_path.write_text("epub final")
        return ConversionResult(epub_path=epub_path, azw3_path=None)

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    response = _post_pdf(client, book_lang="pt")

    assert response.status_code == 202
    assert isinstance(response.json()["job_id"], str)


def test_progress_reports_intermediate_steps_and_completion(monkeypatch, client, tmp_path):
    def _fake_convert_book(pdf_path, on_progress=None, **kwargs):
        for step in ("pdf_to_epub", "dehyphenate"):
            if on_progress:
                on_progress(step)
            time.sleep(0.05)  # dá tempo do teste observar um estado intermediário
        epub_path = tmp_path / "livro.epub"
        epub_path.write_text("epub final")
        return ConversionResult(epub_path=epub_path, azw3_path=None)

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    job_id = _post_pdf(client, book_lang="pt").json()["job_id"]

    observed_steps = set()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        data = client.get(f"/progress/{job_id}").json()
        observed_steps.add(data["step"])
        if data["done"]:
            break
        time.sleep(0.01)

    assert "done" in observed_steps
    assert observed_steps & {"pdf_to_epub", "dehyphenate"}  # pelo menos uma etapa capturada
    assert data["epub"] == "livro.epub"
    assert data["epub_url"] == "/download/livro.epub"
    assert data["azw3"] is None


def test_progress_reports_pipeline_step_error(monkeypatch, client):
    def _fake_convert_book(pdf_path, on_progress=None, **kwargs):
        raise PipelineStepError("pdf_to_epub", RuntimeError("calibre não encontrado"))

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    job_id = _post_pdf(client).json()["job_id"]
    data = _wait_for_done(client, job_id)

    assert data["step"] == "error"
    assert data["status_code"] == 422
    assert "pdf_to_epub" in data["detail"]


def test_progress_reports_value_error_as_400(monkeypatch, client):
    def _fake_convert_book(pdf_path, on_progress=None, **kwargs):
        raise ValueError("book_lang é obrigatório quando translate_to é usado")

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    job_id = _post_pdf(client, translate_to="es").json()["job_id"]
    data = _wait_for_done(client, job_id)

    assert data["step"] == "error"
    assert data["status_code"] == 400


def test_progress_returns_404_for_unknown_job(client):
    response = client.get("/progress/nao-existe")

    assert response.status_code == 404


def test_rejects_non_pdf_upload(monkeypatch, client):
    def _fail(*args, **kwargs):
        raise AssertionError("não deveria chamar o pipeline para arquivo não-PDF")

    monkeypatch.setattr("library_ebooks.app.convert_book", _fail)

    response = client.post(
        "/convert",
        files={"file": ("livro.txt", b"nao e pdf", "text/plain")},
    )

    assert response.status_code == 400


def test_temp_pdf_is_removed_after_job_finishes(monkeypatch, client):
    captured_path = {}

    def _fake_convert_book(pdf_path, on_progress=None, **kwargs):
        captured_path["path"] = Path(pdf_path)
        raise PipelineStepError("pdf_to_epub", RuntimeError("boom"))

    monkeypatch.setattr("library_ebooks.app.convert_book", _fake_convert_book)

    job_id = _post_pdf(client).json()["job_id"]
    _wait_for_done(client, job_id)

    assert not captured_path["path"].exists()


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


# Testes da história #24: endpoint de download dos arquivos gerados.


def test_download_serves_existing_file(monkeypatch, client, tmp_path):
    monkeypatch.setattr("library_ebooks.app.DEFAULT_OUTPUT_DIR", tmp_path)
    (tmp_path / "livro.epub").write_bytes(b"conteudo do epub")

    response = client.get("/download/livro.epub")

    assert response.status_code == 200
    assert response.content == b"conteudo do epub"
    assert "livro.epub" in response.headers["content-disposition"]


def test_download_returns_404_for_missing_file(monkeypatch, client, tmp_path):
    monkeypatch.setattr("library_ebooks.app.DEFAULT_OUTPUT_DIR", tmp_path)

    response = client.get("/download/naoexiste.epub")

    assert response.status_code == 404


def test_download_blocks_path_traversal(monkeypatch, client, tmp_path):
    monkeypatch.setattr("library_ebooks.app.DEFAULT_OUTPUT_DIR", tmp_path)
    outside_dir = tmp_path.parent / "segredo"
    outside_dir.mkdir(exist_ok=True)
    (outside_dir / "secreto.txt").write_text("não devia sair daqui")

    response = client.get("/download/..%2Fsegredo%2Fsecreto.txt")

    assert response.status_code == 404


def test_safe_filename_strips_path_components():
    from library_ebooks.app import _safe_filename

    assert _safe_filename("../../etc/passwd") == "passwd"
    assert _safe_filename("livro.epub") == "livro.epub"


def test_app_js_renders_download_links():
    from library_ebooks.app import _STATIC_DIR

    body = (_STATIC_DIR / "app.js").read_text()
    assert "epub_url" in body
    assert "azw3_url" in body
    assert "download" in body


# Testes da história #25: feedback de progresso na UI.


def test_index_page_has_progress_indicator(client):
    body = client.get("/").text

    assert 'id="progress"' in body


def test_app_js_polls_progress_endpoint(client):
    body = (Path(__file__).parent.parent / "src/library_ebooks/static/app.js").read_text()

    assert "/progress/" in body
    assert "job_id" in body
