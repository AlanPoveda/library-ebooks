"""Orquestra o pipeline completo de conversão de um livro.

PDF -> EPUB (Calibre) -> dehyphenate -> verificação gramatical opcional
-> tradução opcional -> AZW3 opcional (Calibre). Ver `PLANNING.md` pro
desenho completo.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .convert import convert_epub_to_azw3, convert_pdf_to_epub
from .dehyphenate import dehyphenate_epub
from .lint import correct_epub, format_lint_report, lint_epub
from .translate import translate_epub

logger = logging.getLogger(__name__)

# Local padrão de entrada/saída quando o chamador não passa output_dir
# explícito — ver PLANNING.md (pasta gitignored, não versiona ebooks).
DEFAULT_OUTPUT_DIR = Path("books")

_VALID_GRAMMAR_CHECK_WHEN = {"before_translate", "after_translate"}


@dataclass
class ConversionResult:
    """Caminhos dos arquivos finais gerados pelo pipeline."""

    epub_path: Path
    azw3_path: Path | None = None
    lint_report_path: Path | None = None


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


def _run_step(
    step: str,
    description: str,
    func: Callable,
    *args,
    on_progress: Callable[[str], None] | None = None,
    **kwargs,
):
    if on_progress is not None:
        on_progress(step)
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
    check_grammar: bool = False,
    grammar_check_when: str = "before_translate",
    on_progress: Callable[[str], None] | None = None,
) -> ConversionResult:
    """Roda o pipeline completo sobre um PDF e retorna os arquivos finais.

    `output_dir` default pra `books/` (relativo ao diretório de trabalho)
    quando não informado. `book_lang` é o idioma em que o livro já está
    escrito — usado pra validação por dicionário na correção de
    hifenização, como idioma de origem se `translate_to` for passado, e
    pro LanguageTool se `check_grammar` for passado (nesses dois casos é
    obrigatório). `translate_to` deve ser um dos idiomas de destino
    suportados (es/en/pt) — validado dentro de `translate_epub`.

    `check_grammar` liga a etapa opcional de verificação gramatical
    (LanguageTool local, épico 6): aplica automaticamente as correções
    de alta confiança e, se sobrar algum problema, salva um relatório em
    `{stem}.lint.txt`. `grammar_check_when` ("before_translate" ou
    "after_translate") controla se ela roda antes ou depois da tradução.

    `on_progress`, se passado, é chamado com o nome de cada etapa
    ("pdf_to_epub", "dehyphenate", "grammar_check", "translate",
    "epub_to_azw3") no instante em que ela começa a rodar — pro
    chamador (ex.: o app web) reportar progresso em tempo real.

    Arquivos puramente intermediários (o EPUB "bruto" recém-saído do
    Calibre, e cada EPUB que vira entrada de uma etapa seguinte) são
    apagados ao longo do processo — só os arquivos finais (EPUB,
    opcionalmente AZW3, opcionalmente o relatório de gramática)
    permanecem em `output_dir`.
    """
    if translate_to is not None and book_lang is None:
        raise ValueError(
            "book_lang é obrigatório quando translate_to é usado "
            "(precisa saber o idioma de origem do livro pra traduzir)."
        )
    if check_grammar and book_lang is None:
        raise ValueError(
            "book_lang é obrigatório quando check_grammar é usado "
            "(precisa saber o idioma do livro pra verificar a gramática)."
        )
    if grammar_check_when not in _VALID_GRAMMAR_CHECK_WHEN:
        raise ValueError(
            f"grammar_check_when inválido: {grammar_check_when!r} "
            f"(use um de {sorted(_VALID_GRAMMAR_CHECK_WHEN)})"
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
        on_progress=on_progress,
    )

    clean_epub_path = output_dir / f"{stem}.epub"
    _run_step(
        "dehyphenate",
        "Corrigindo hifenização",
        dehyphenate_epub,
        raw_epub_path,
        clean_epub_path,
        lang=book_lang,
        on_progress=on_progress,
    )
    raw_epub_path.unlink()

    final_epub_path = clean_epub_path

    if check_grammar and grammar_check_when == "before_translate":
        final_epub_path = _run_grammar_check(
            final_epub_path, output_dir, stem, book_lang, on_progress
        )

    if translate_to is not None:
        translated_path = output_dir / f"{stem}.{translate_to}.epub"
        _run_step(
            "translate",
            f"Traduzindo para {translate_to}",
            translate_epub,
            final_epub_path,
            translated_path,
            book_lang,
            translate_to,
            on_progress=on_progress,
        )
        final_epub_path.unlink()  # era só intermediário pra chegar na tradução
        final_epub_path = translated_path

    if check_grammar and grammar_check_when == "after_translate":
        final_epub_path = _run_grammar_check(
            final_epub_path, output_dir, stem, book_lang, on_progress
        )

    lint_report_path = None
    if check_grammar:
        lint_report_path = _write_lint_report(final_epub_path, output_dir, stem, book_lang)

    azw3_path = None
    if generate_azw3:
        azw3_path = final_epub_path.with_suffix(".azw3")
        _run_step(
            "epub_to_azw3",
            "Gerando AZW3",
            convert_epub_to_azw3,
            final_epub_path,
            azw3_path,
            on_progress=on_progress,
        )

    return ConversionResult(
        epub_path=final_epub_path, azw3_path=azw3_path, lint_report_path=lint_report_path
    )


def _run_grammar_check(
    current_epub_path: Path,
    output_dir: Path,
    stem: str,
    book_lang: str,
    on_progress: Callable[[str], None] | None,
) -> Path:
    """Roda a etapa de correção gramatical (alta confiança) sobre o EPUB
    atual, apaga o EPUB que virou intermediário e retorna o caminho do
    novo EPUB revisado."""
    checked_path = output_dir / f"{stem}.checked.epub"
    _run_step(
        "grammar_check",
        "Verificando gramática",
        correct_epub,
        current_epub_path,
        checked_path,
        book_lang,
        on_progress=on_progress,
    )
    current_epub_path.unlink()
    return checked_path


def _write_lint_report(
    epub_path: Path, output_dir: Path, stem: str, book_lang: str
) -> Path | None:
    """Gera o relatório do que sobrou sem correção automática (ver
    `lint_epub`), salvando em `{stem}.lint.txt` só se houver algo a
    reportar. Uma falha aqui não deve derrubar uma conversão que já deu
    certo — só fica sem relatório, com aviso no log."""
    try:
        reports = lint_epub(epub_path, lang=book_lang)
    except Exception:
        logger.exception("Falha ao gerar relatório de gramática (conversão não é afetada)")
        return None

    if not reports:
        return None

    report_path = output_dir / f"{stem}.lint.txt"
    report_path.write_text(format_lint_report(reports), encoding="utf-8")
    return report_path
