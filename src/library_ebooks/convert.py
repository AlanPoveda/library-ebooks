"""Localização e invocação do `ebook-convert` do Calibre.

O Calibre é o motor usado para converter PDF -> EPUB e EPUB -> AZW3
(ver `PLANNING.md`). No macOS, instalar o app não coloca os binários
de linha de comando no PATH por padrão — eles ficam dentro do bundle.
"""

import shutil
from pathlib import Path

_MACOS_BUNDLE_PATH = Path("/Applications/calibre.app/Contents/MacOS/ebook-convert")


class CalibreNotFoundError(RuntimeError):
    """Levantado quando o ebook-convert do Calibre não é encontrado."""


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
