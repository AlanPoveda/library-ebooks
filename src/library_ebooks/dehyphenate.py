"""Correção de hifenização quebrada vinda da extração de PDF.

Quando um PDF com texto justificado é extraído, palavras que caíram no
fim da linha ficam com um hífen seguido de quebra de linha, ex.:
"informa-\\nção". Este módulo reconstitui a palavra original.
"""

import re

# Hífen imediatamente seguido de quebra de linha, com caractere de
# palavra (letra/dígito/underscore, incluindo acentuados) de cada lado.
# Hífens sem quebra de linha logo em seguida (ex.: "bom-mas-ruim") não
# são tocados.
_BROKEN_WORD_PATTERN = re.compile(r"(?<=\w)-\n(?=\w)", re.UNICODE)


def join_broken_words(text: str) -> str:
    """Junta palavras quebradas por hífen no fim de linha.

    Ex.: "informa-\\nção" -> "informação"

    Não faz validação por dicionário (isso fica pra história #7) — só
    remove o hífen quando ele está imediatamente seguido de quebra de
    linha entre dois caracteres de palavra.
    """
    return _BROKEN_WORD_PATTERN.sub("", text)
