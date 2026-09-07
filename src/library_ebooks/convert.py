"""Localização e invocação do `ebook-convert` do Calibre.

O Calibre é o motor usado para converter PDF -> EPUB e EPUB -> AZW3
(ver `PLANNING.md`). No macOS, instalar o app não coloca os binários
de linha de comando no PATH por padrão — eles ficam dentro do bundle.
No Windows, o instalador do Calibre também não adiciona ao PATH por
padrão, e usa "Calibre2" como nome de pasta mesmo em instalações novas
(peculiaridade histórica do instalador).
"""

import shutil
import subprocess
from pathlib import Path

# Caminhos conhecidos de instalação, checados em ordem quando o
# ebook-convert não está no PATH. Cada SO só bate um desses — os outros
# simplesmente não existem na máquina, o que é esperado.
_KNOWN_INSTALL_PATHS = [
    Path("/Applications/calibre.app/Contents/MacOS/ebook-convert"),  # macOS
    Path(r"C:\Program Files\Calibre2\ebook-convert.exe"),  # Windows 64-bit
    Path(r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"),  # Windows 32-bit
]


class CalibreNotFoundError(RuntimeError):
    """Levantado quando o ebook-convert do Calibre não é encontrado."""


class ConversionError(RuntimeError):
    """Levantado quando o ebook-convert falha ao converter um arquivo."""


def find_ebook_convert() -> str:
    """Localiza o executável `ebook-convert` do Calibre.

    Procura primeiro no PATH; se não achar, tenta os caminhos padrão de
    instalação conhecidos (macOS e Windows — ver `_KNOWN_INSTALL_PATHS`).
    Levanta `CalibreNotFoundError` com uma mensagem acionável se não
    encontrar em nenhum lugar.
    """
    path_match = shutil.which("ebook-convert")
    if path_match:
        return path_match

    for candidate in _KNOWN_INSTALL_PATHS:
        if candidate.is_file():
            return str(candidate)

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
