"""Verificação gramatical/estilo via LanguageTool local (épico 6).

Diferente do dicionário usado no dehyphenate (que só valida se uma
palavra existe), aqui verificamos gramática/estilo de verdade —
concordância, crase, pontuação, repetição etc. Roda um servidor
LanguageTool local (via `language_tool_python`, que sobe uma JVM na
máquina), sem nenhuma chamada externa.
"""

from dataclasses import dataclass

import language_tool_python

# Códigos de idioma simples usados no resto do app (es/en/pt) mapeados
# pros códigos de idioma do LanguageTool.
_LANGUAGE_TOOL_CODES = {"pt": "pt-BR", "es": "es", "en": "en-US"}


@dataclass
class GrammarIssue:
    """Um problema encontrado pelo LanguageTool num texto."""

    offset: int
    length: int
    message: str
    rule_id: str
    replacements: list[str]


def check_text(text: str, lang: str) -> list[GrammarIssue]:
    """Verifica um texto com o LanguageTool local, retornando os
    problemas encontrados (posição, regra, mensagem, sugestões).

    `lang` é um dos códigos simples do app ("pt", "es" ou "en").
    """
    if lang not in _LANGUAGE_TOOL_CODES:
        raise ValueError(
            f"idioma não suportado: {lang!r} (use um de {sorted(_LANGUAGE_TOOL_CODES)})"
        )

    tool = language_tool_python.LanguageTool(_LANGUAGE_TOOL_CODES[lang])
    try:
        matches = tool.check(text)
    finally:
        tool.close()

    return [
        GrammarIssue(
            offset=match.offset,
            length=match.error_length,
            message=match.message,
            rule_id=match.rule_id,
            replacements=match.replacements,
        )
        for match in matches
    ]
