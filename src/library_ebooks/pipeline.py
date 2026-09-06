"""Orquestra o pipeline completo de conversão de um livro.

PDF -> EPUB (Calibre) -> dehyphenate -> tradução opcional -> AZW3
opcional (Calibre). Ver `PLANNING.md` pro desenho completo — a etapa de
verificação gramatical (épico 6) ainda não está integrada aqui; quando
existir, entra entre o dehyphenate e a tradução.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .convert import convert_epub_to_azw3, convert_pdf_to_epub
from .dehyphenate import dehyphenate_epub
from .translate import translate_epub

logger = logging.getLogger(__name__)

# Local padrão de entrada/saída quando o chamador não passa output_dir
# explícito — ver PLANNING.md (pasta gitignored, não versiona ebooks).
DEFAULT_OUTPUT_DIR = Path("books")


@dataclass
class ConversionResult:
    """Caminhos dos arquivos finais gerados pelo pipeline."""

    epub_path: Path
    azw3_path: Path | None = None


class PipelineStepError(RuntimeError):
    """Levantado quando uma etapa do pipeline falha.

    Identifica qual etapa foi (`step`) e preserva o erro original em
    `original` (e como `__cause__`, via `raise ... from`), pra quem
    trata o erro (ex.: o app web) poder mostrar uma mensagem clara sem
    precisar conhecer as exceções específicas de cada módulo.
    """

    def __init__(self, step: str, original: Exception):
        self.step = step
        self.original = original
        super().__init__(f"Falha na etapa '{step}': {original}")


def _run_step(step: str, description: str, func: Callable, *args, **kwargs):
    logger.info("%s...", description)
    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        logger.error("Falha na etapa %r: %s", step, exc)
        raise PipelineStepError(step, exc) from exc
    logger.info("%s: concluído.", description)
    return result


def convert_book(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    book_lang: str | None = None,
    translate_to: str | None = None,
    generate_azw3: bool = False,
) -> ConversionResult:
    """Roda o pipeline completo sobre um PDF e retorna os arquivos finais.

    `output_dir` default pra `books/` (relativo ao diretório de trabalho)
    quando não informado. `book_lang` é o idioma em que o livro já está
    escrito — usado tanto pra validação por dicionário na correção de
    hifenização quanto como idioma de origem se `translate_to` for
    passado (nesse caso é obrigatório). `translate_to` deve ser um dos
    idiomas de destino suportados (es/en/pt) — validado dentro de
    `translate_epub`.

    Arquivos puramente intermediários (o EPUB "bruto" recém-saído do
    Calibre, e o EPUB "limpo" pré-tradução quando há tradução) são
    apagados ao longo do processo — só os arquivos finais (EPUB e,
    opcionalmente, AZW3) permanecem em `output_dir`.
    """
    if translate_to is not None and book_lang is None:
        raise ValueError(
            "book_lang é obrigatório quando translate_to é usado "
            "(precisa saber o idioma de origem do livro pra traduzir)."
        )

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem

    raw_epub_path = output_dir / f"{stem}.raw.epub"
    _run_step(
        "pdf_to_epub",
        f"Convertendo {pdf_path.name} para EPUB",
        convert_pdf_to_epub,
        pdf_path,
        raw_epub_path,
    )

    clean_epub_path = output_dir / f"{stem}.epub"
    _run_step(
        "dehyphenate",
        "Corrigindo hifenização",
        dehyphenate_epub,
        raw_epub_path,
        clean_epub_path,
        lang=book_lang,
    )
    raw_epub_path.unlink()

    final_epub_path = clean_epub_path
    if translate_to is not None:
        translated_path = output_dir / f"{stem}.{translate_to}.epub"
        _run_step(
            "translate",
            f"Traduzindo para {translate_to}",
            translate_epub,
            clean_epub_path,
            translated_path,
            book_lang,
            translate_to,
        )
        clean_epub_path.unlink()  # era só intermediário pra chegar na tradução
        final_epub_path = translated_path

    azw3_path = None
    if generate_azw3:
        azw3_path = final_epub_path.with_suffix(".azw3")
        _run_step(
            "epub_to_azw3",
            "Gerando AZW3",
            convert_epub_to_azw3,
            final_epub_path,
            azw3_path,
        )

    return ConversionResult(epub_path=final_epub_path, azw3_path=azw3_path)
