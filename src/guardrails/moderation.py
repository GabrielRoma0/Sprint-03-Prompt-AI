"""
Guardrail de moderação — detecta tentativas de jailbreak e prompt
injection antes de a mensagem chegar à chain LCEL.

Aula transversal / §6 do enunciado da Sprint 03.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ResultadoModeracao:
    seguro: bool
    motivo: str | None = None
    mensagem_usuario: str | None = None


# Cada padrão cobre uma família de ataque comum. Comentários indicam a
# intenção por trás do padrão para facilitar manutenção/expansão pelo grupo.
_PADROES_JAILBREAK = [
    # Tenta anular instruções anteriores do sistema.
    re.compile(r"\bignor[ea]\s+(todas\s+)?as\s+instru[çc][õo]es\s+anteriores\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(all\s+)?previous\s+instructions\b", re.IGNORECASE),
    # Tenta trocar a persona/restrições do assistente.
    re.compile(r"\bfinja\s+que\s+voc[êe]\s+[ée]\b", re.IGNORECASE),
    re.compile(r"\bmodo\s+(desenvolvedor|dev|sem\s+restri[çc][õo]es|dan)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(dan|an\s+unrestricted\s+ai)\b", re.IGNORECASE),
    # Tenta extrair o system prompt.
    re.compile(r"\b(repita|mostre|revele)\s+(o\s+)?(seu\s+)?(system\s+)?prompt\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(is|are)\s+your\s+(system\s+)?instructions\b", re.IGNORECASE),
    # Tenta injetar instruções via delimitadores fake de sistema.
    re.compile(r"\[\s*system\s*\]", re.IGNORECASE),
    re.compile(r"</?\s*system\s*>", re.IGNORECASE),
]


def detectar_jailbreak(texto_usuario: str) -> ResultadoModeracao:
    """
    Verifica se a mensagem do usuário contém um padrão conhecido de
    jailbreak/prompt injection.

    Retorna `seguro=False` e uma mensagem de recusa padrão quando detecta
    um padrão suspeito. Não revela ao usuário qual padrão foi detectado
    (evita ensinar como contornar o guardrail).
    """
    for padrao in _PADROES_JAILBREAK:
        if padrao.search(texto_usuario):
            return ResultadoModeracao(
                seguro=False,
                motivo="padrao_jailbreak_detectado",
                mensagem_usuario=(
                    "Não posso seguir essa instrução. Posso ajudar com "
                    "consultas sobre carregadores GoodWe, estado de recarga "
                    "e faturamento — como posso ajudar dentro desse escopo?"
                ),
            )

    return ResultadoModeracao(seguro=True)


def pipeline_guardrails(texto_usuario: str):
    """
    Ponto único de entrada: roda moderação (jailbreak) e, se passar,
    delega para a validação de escopo em scope_validator.py.

    Import local para evitar dependência circular caso scope_validator
    também precise importar algo deste módulo no futuro.
    """
    from src.guardrails.scope_validator import validar_escopo

    moderacao = detectar_jailbreak(texto_usuario)
    if not moderacao.seguro:
        return moderacao

    return validar_escopo(texto_usuario)
