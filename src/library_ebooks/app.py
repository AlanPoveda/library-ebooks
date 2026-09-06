"""App web local: recebe o PDF arrastado e dispara o pipeline.

Ver `PLANNING.md` — app web local (FastAPI + frontend simples), sem
depender de nenhum serviço externo.
"""

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import DEFAULT_OUTPUT_DIR, PipelineStepError, convert_book

app = FastAPI(title="Library Ebooks")

_STATIC_DIR = Path(__file__).parent / "static"


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    book_lang: str | None = Form(None),
    translate_to: str | None = Form(None),
    generate_azw3: bool = Form(False),
):
    """Recebe um PDF, salva num diretório temporário e roda o pipeline.

    O PDF enviado é apagado ao final da requisição (sucesso ou erro) —
    só os arquivos finais gerados pelo pipeline (em `books/`) persistem.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="envie um arquivo PDF (.pdf)")

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / file.filename
        pdf_path.write_bytes(await file.read())

        try:
            result = convert_book(
                pdf_path,
                book_lang=book_lang,
                translate_to=translate_to,
                generate_azw3=generate_azw3,
            )
        except PipelineStepError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "epub": result.epub_path.name,
        "epub_url": f"/download/{result.epub_path.name}",
        "azw3": result.azw3_path.name if result.azw3_path else None,
        "azw3_url": f"/download/{result.azw3_path.name}" if result.azw3_path else None,
    }


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
