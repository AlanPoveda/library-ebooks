"""App web local: recebe o PDF arrastado e dispara o pipeline.

Ver `PLANNING.md` — app web local (FastAPI + frontend simples), sem
depender de nenhum serviço externo.
"""

import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import DEFAULT_OUTPUT_DIR, PipelineStepError, convert_book

app = FastAPI(title="Library Ebooks")

_STATIC_DIR = Path(__file__).parent / "static"

# Estado dos jobs de conversão em andamento, pra história #25 (feedback
# de progresso): o app é local/single-user, então um dict em memória
# (sem persistência) é suficiente — não sobrevive a um restart do
# processo, o que é aceitável aqui.
_jobs: dict[str, dict] = {}


def _run_conversion_job(job_id: str, pdf_bytes: bytes, filename: str, **pipeline_kwargs):
    """Roda o pipeline numa thread separada, atualizando `_jobs[job_id]`
    a cada etapa — é isso que permite ao GET /progress/{job_id} reportar
    em qual etapa o processamento está enquanto ele roda."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / filename
        pdf_path.write_bytes(pdf_bytes)

        def _on_progress(step: str):
            _jobs[job_id] = {"step": step, "done": False}

        try:
            result = convert_book(pdf_path, on_progress=_on_progress, **pipeline_kwargs)
        except PipelineStepError as exc:
            _jobs[job_id] = {
                "step": "error",
                "done": True,
                "status_code": 422,
                "detail": str(exc),
            }
            return
        except ValueError as exc:
            _jobs[job_id] = {
                "step": "error",
                "done": True,
                "status_code": 400,
                "detail": str(exc),
            }
            return

    _jobs[job_id] = {
        "step": "done",
        "done": True,
        "epub": result.epub_path.name,
        "epub_url": f"/download/{result.epub_path.name}",
        "azw3": result.azw3_path.name if result.azw3_path else None,
        "azw3_url": f"/download/{result.azw3_path.name}" if result.azw3_path else None,
    }


@app.post("/convert", status_code=202)
async def convert(
    file: UploadFile = File(...),
    book_lang: str | None = Form(None),
    translate_to: str | None = Form(None),
    generate_azw3: bool = Form(False),
    check_grammar: bool = Form(False),
):
    """Recebe um PDF e dispara o pipeline em background.

    Retorna de cara um `job_id` — o progresso e o resultado final são
    consultados via `GET /progress/{job_id}` (história #25). O PDF
    enviado é lido aqui e salvo num diretório temporário só dentro da
    thread do job, apagado ao final (sucesso ou erro).
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="envie um arquivo PDF (.pdf)")

    pdf_bytes = await file.read()
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"step": "queued", "done": False}

    thread = threading.Thread(
        target=_run_conversion_job,
        args=(job_id, pdf_bytes, file.filename),
        kwargs={
            "book_lang": book_lang,
            "translate_to": translate_to,
            "generate_azw3": generate_azw3,
            "check_grammar": check_grammar,
        },
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id}


@app.get("/progress/{job_id}")
async def progress(job_id: str):
    """Estado atual de um job de conversão (ver `_run_conversion_job`)."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job não encontrado")
    return job


def _safe_filename(filename: str) -> str:
    """Descarta qualquer componente de diretório do nome do arquivo,
    prevenindo path traversal (ex.: "../../etc/passwd" -> "passwd")."""
    return Path(filename).name


@app.get("/download/{filename}")
async def download(filename: str):
    """Serve pra download um arquivo final gerado pelo pipeline (em
    `books/`). Restrito a essa pasta — não serve nenhum outro caminho."""
    file_path = DEFAULT_OUTPUT_DIR / _safe_filename(filename)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="arquivo não encontrado")
    return FileResponse(file_path, filename=file_path.name)


# Frontend estático (index.html com a área de drag-and-drop, app.js,
# style.css). Montado por último pra não sombrear a rota /convert acima.
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
