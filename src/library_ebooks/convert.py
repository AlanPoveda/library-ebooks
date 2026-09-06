"""Localização e invocação do `ebook-convert` do Calibre.

O Calibre é o motor usado para converter PDF -> EPUB e EPUB -> AZW3
(ver `PLANNING.md`). No macOS, instalar o app não coloca os binários
de linha de comando no PATH por padrão — eles ficam dentro do bundle.
"""

import shutil
import subprocess
from pathlib import Path

_MACOS_BUNDLE_PATH = Path("/Applications/calibre.app/Contents/MacOS/ebook-convert")


class CalibreNotFoundError(RuntimeError):
    """Levantado quando o ebook-convert do Calibre não é encontrado."""


class ConversionError(RuntimeError):
    """Levantado quando o ebook-convert falha ao converter um arquivo."""


def find_ebook_convert() -> str:
    """Localiza o executável `ebook-convert` do Calibre.

    Procura primeiro no PATH; se não achar, tenta o caminho padrão do
    bundle do Calibre no macOS. Levanta `CalibreNotFoundError` com uma
    mensagem acionável se não encontrar em nenhum dos dois lugares.
    """
    path_match = shutil.which("ebook-convert")
    if path_match:
        return path_match

    if _MACOS_BUNDLE_PATH.is_file():
        return str(_MACOS_BUNDLE_PATH)

    raise CalibreNotFoundError(
        "ebook-convert não encontrado. Instale o Calibre "
        "(https://calibre-ebook.com/) ou adicione o ebook-convert ao PATH."
    )


def _run_ebook_convert(
    input_path: str | Path, output_path: str | Path, target_format_label: str
) -> Path:
    """Chama o ebook-convert do Calibre e trata os erros comuns.

    Levanta `CalibreNotFoundError` se o Calibre não estiver disponível, e
    `ConversionError` (com o stderr do Calibre) se a conversão falhar.
    """
    ebook_convert = find_ebook_convert()
    try:
        subprocess.run(
            [ebook_convert, str(input_path), str(output_path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise ConversionError(
            f"Falha ao converter {input_path} para {target_format_label}: "
            f"{stderr.strip()}"
        ) from exc
    return Path(output_path)


def convert_pdf_to_epub(pdf_path: str | Path, epub_path: str | Path) -> Path:
    """Converte um PDF em EPUB usando o ebook-convert do Calibre."""
    return _run_ebook_convert(pdf_path, epub_path, "EPUB")


def convert_epub_to_azw3(epub_path: str | Path, azw3_path: str | Path) -> Path:
    """Converte um EPUB em AZW3 (formato opcional no download, para Kindle)
    usando o ebook-convert do Calibre."""
    return _run_ebook_convert(epub_path, azw3_path, "AZW3")
