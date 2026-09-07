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

# Sugestões de estilo são preferência subjetiva de redação, não erro —
# nunca aplicadas automaticamente, independente de quantas sugestões têm.
_UNSAFE_ISSUE_TYPES = {"style"}


@dataclass
class GrammarIssue:
    """Um problema encontrado pelo LanguageTool num texto."""

    offset: int
    length: int
    message: str
    rule_id: str
    replacements: list[str]
    issue_type: str


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
            issue_type=match.rule_issue_type,
        )
        for match in matches
    ]


def _is_high_confidence(issue: GrammarIssue) -> bool:
    """Considera seguro corrigir automaticamente:

    - Erros ortográficos ("misspelling"): o corretor quase sempre devolve
      várias sugestões rankeadas mesmo pra erros óbvios (ex.:
      "concordancia" -> concordância/concordança/...), então usamos a
      primeira sempre que houver ao menos uma sugestão.
    - Qualquer outra regra que não seja de estilo (sugestão de estilo é
      preferência, não erro), desde que tenha uma única sugestão — sem
      ambiguidade de qual escolher (ex.: concordância simples).
    """
    if issue.issue_type == "misspelling":
        return bool(issue.replacements)
    if issue.issue_type in _UNSAFE_ISSUE_TYPES:
        return False
    return len(issue.replacements) == 1


def apply_high_confidence_corrections(
    text: str, issues: list[GrammarIssue]
) -> tuple[str, list[GrammarIssue]]:
    """Aplica automaticamente as correções de alta confiança (ver
    `_is_high_confidence`) e retorna `(texto_corrigido, problemas_restantes)`.

    Os problemas restantes (ambíguos ou de estilo) não alteram o texto —
    ficam só pro relatório. Aplicado de trás pra frente (maior offset
    primeiro) pra uma correção não invalidar o offset das anteriores.
    """
    remaining: list[GrammarIssue] = []
    corrected = text
    for issue in sorted(issues, key=lambda i: i.offset, reverse=True):
        if _is_high_confidence(issue):
            start, end = issue.offset, issue.offset + issue.length
            corrected = corrected[:start] + issue.replacements[0] + corrected[end:]
        else:
            remaining.append(issue)
    remaining.reverse()  # devolve na ordem de leitura (offset crescente)
    return corrected, remaining
