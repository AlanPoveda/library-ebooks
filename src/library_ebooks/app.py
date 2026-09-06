"""App web local: recebe o PDF arrastado e dispara o pipeline.

Ver `PLANNING.md` — app web local (FastAPI + frontend simples), sem
depender de nenhum serviço externo.
"""

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .pipeline import PipelineStepError, convert_book

app = FastAPI(title="Library Ebooks")


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
        "azw3": result.azw3_path.name if result.azw3_path else None,
    }
