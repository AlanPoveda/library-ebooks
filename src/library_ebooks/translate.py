"""Tradução offline via Argos Translate.

Todo o processamento roda localmente: os modelos de idioma são baixados
uma vez (na primeira vez que um par é usado) e ficam instalados na
máquina, sem depender de chamadas externas depois disso.
"""

import argostranslate.package as argos_package


class TranslationPackageError(RuntimeError):
    """Levantado quando um pacote de idioma do Argos Translate não pode
    ser instalado (o par não existe no índice local nem no remoto)."""


def _is_installed(from_code: str, to_code: str) -> bool:
    return any(
        pkg.from_code == from_code and pkg.to_code == to_code
        for pkg in argos_package.get_installed_packages()
    )


def ensure_package_installed(from_code: str, to_code: str) -> None:
    """Garante que o pacote de tradução `from_code` -> `to_code` está
    instalado localmente, baixando-o se necessário.

    Levanta `TranslationPackageError` se o par não existir no índice do
    Argos Translate.
    """
    if _is_installed(from_code, to_code):
        return

    argos_package.update_package_index()
    installed = argos_package.install_package_for_language_pair(from_code, to_code)
    if not installed:
        raise TranslationPackageError(
            f"Não existe pacote de tradução direto de {from_code!r} para "
            f"{to_code!r} no Argos Translate."
        )
