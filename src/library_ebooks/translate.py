"""Tradução offline via Argos Translate.

Todo o processamento roda localmente: os modelos de idioma são baixados
uma vez (na primeira vez que um par é usado) e ficam instalados na
máquina, sem depender de chamadas externas depois disso.
"""

from pathlib import Path

import argostranslate.package as argos_package
import argostranslate.translate as argos_translate

from .epub_utils import apply_to_epub_text_nodes


class TranslationPackageError(RuntimeError):
    """Levantado quando um pacote de idioma do Argos Translate não pode
    ser instalado (o par não existe no índice local nem no remoto)."""


class UnsupportedLanguageError(ValueError):
    """Levantado quando um idioma de destino fora dos suportados pelo
    app (es/en/pt) é pedido."""


# Idiomas de destino que o app oferece pro usuário escolher (mesmos do
# épico de tradução no PLANNING.md). O idioma de origem não é restrito
# a esses três — é o idioma em que o livro já está escrito.
SUPPORTED_TARGET_LANGUAGES = frozenset({"es", "en", "pt"})


def validate_target_language(lang: str) -> str:
    """Valida que `lang` é um dos idiomas de destino suportados (es/en/pt).

    Retorna o próprio código se válido; levanta `UnsupportedLanguageError`
    com uma mensagem acionável caso contrário.
    """
    if lang not in SUPPORTED_TARGET_LANGUAGES:
        raise UnsupportedLanguageError(
            f"idioma de destino não suportado: {lang!r} "
            f"(use um de {sorted(SUPPORTED_TARGET_LANGUAGES)})"
        )
    return lang


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


_PIVOT_LANG = "en"


def translate_text(
    text: str, from_code: str, to_code: str, pivot_code: str = _PIVOT_LANG
) -> str:
    """Traduz um texto, com fallback de pivô de idioma.

    Tenta o par direto primeiro; se não existir pacote pra ele, tenta
    traduzir em duas etapas passando pelo `pivot_code` (inglês por
    padrão) — ex.: pt->es vira pt->en->es quando pt->es não existe.

    Levanta `TranslationPackageError` se nem o par direto nem as duas
    etapas do pivô estiverem disponíveis, ou se um dos dois idiomas já
    for o próprio pivô (nesse caso não há fallback possível).
    """
    try:
        ensure_package_installed(from_code, to_code)
    except TranslationPackageError:
        if pivot_code in (from_code, to_code):
            raise
        ensure_package_installed(from_code, pivot_code)
        ensure_package_installed(pivot_code, to_code)
        intermediate = argos_translate.translate(text, from_code, pivot_code)
        return argos_translate.translate(intermediate, pivot_code, to_code)

    return argos_translate.translate(text, from_code, to_code)


def translate_epub(
    input_path: str | Path,
    output_path: str | Path,
    from_code: str,
    to_code: str,
) -> Path:
    """Traduz todo o texto de um EPUB, preservando tags e estrutura HTML.

    Percorre os documentos internos traduzindo cada nó de texto (nós só
    com espaço em branco são pulados) via `translate_text` — incluindo o
    fallback de pivô de idioma quando não houver par direto — e recoloca
    a tradução no lugar, sem alterar a marcação.

    Levanta `UnsupportedLanguageError` de cara se `to_code` não for um
    dos idiomas de destino suportados (es/en/pt), antes de tentar
    instalar qualquer pacote ou traduzir qualquer texto.
    """
    validate_target_language(to_code)
    return apply_to_epub_text_nodes(
        input_path,
        output_path,
        lambda text: translate_text(text, from_code, to_code),
    )
