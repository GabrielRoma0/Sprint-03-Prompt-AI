"""
Guardrail de escopo — garante que o chatbot fica dentro do domínio GoodWe
e recusa domínios sensíveis (jurídico, financeiro, segurança elétrica)
sem orientar a um profissional habilitado.

Aula transversal / §6 do enunciado da Sprint 03.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class MotivoRecusa(str, Enum):
    FORA_DE_ESCOPO_JURIDICO = "fora_de_escopo_juridico"
    FORA_DE_ESCOPO_FINANCEIRO = "fora_de_escopo_financeiro"
    FORA_DE_ESCOPO_ELETRICO = "fora_de_escopo_eletrico"
    ESPECIFICACAO_NAO_VERIFICADA = "especificacao_nao_verificada"


@dataclass
class ResultadoValidacaoEscopo:
    permitido: bool
    motivo: MotivoRecusa | None = None
    mensagem_usuario: str | None = None


# Padrões simples baseados em palavras-chave. Em produção isso poderia ser
# substituído por um classificador leve, mas para os fins da Sprint 03
# (guardrail determinístico e auditável) regex é suficiente e explicável.
_PADROES_JURIDICO = re.compile(
    r"\b(processo|processar|ação judicial|advogad[oa]|contrato jurídico|"
    r"direitos do consumidor|indeniza[çc][ãa]o)\b",
    re.IGNORECASE,
)

_PADROES_FINANCEIRO = re.compile(
    r"\b(investir|investimento|financiamento|empr[ée]stimo|vale a pena comprar "
    r"ações|declarar no imposto de renda|dedu[çc][ãa]o fiscal)\b",
    re.IGNORECASE,
)

_PADROES_ELETRICO = re.compile(
    r"\b(fazer a instala[çc][ãa]o el[ée]trica|ligar sozinho na rede|mexer no "
    r"disjuntor|desmontar o carregador|abrir o equipamento|risco de choque, "
    r"o que eu fa[çc]o)\b",
    re.IGNORECASE,
)


def validar_escopo(texto_usuario: str) -> ResultadoValidacaoEscopo:
    """
    Verifica se a mensagem do usuário pede algo fora do escopo GoodWe
    (jurídico, financeiro ou segurança elétrica) e retorna uma mensagem
    de recusa orientando a buscar um profissional habilitado quando
    aplicável.
    """
    if _PADROES_JURIDICO.search(texto_usuario):
        return ResultadoValidacaoEscopo(
            permitido=False,
            motivo=MotivoRecusa.FORA_DE_ESCOPO_JURIDICO,
            mensagem_usuario=(
                "Não posso dar aconselhamento jurídico. Para questões sobre "
                "processos, contratos ou direitos do consumidor, recomendo "
                "procurar um advogado habilitado."
            ),
        )

    if _PADROES_FINANCEIRO.search(texto_usuario):
        return ResultadoValidacaoEscopo(
            permitido=False,
            motivo=MotivoRecusa.FORA_DE_ESCOPO_FINANCEIRO,
            mensagem_usuario=(
                "Não posso dar aconselhamento financeiro (investimentos, "
                "financiamentos ou questões fiscais). Recomendo consultar um "
                "profissional de finanças ou contabilidade habilitado."
            ),
        )

    if _PADROES_ELETRICO.search(texto_usuario):
        return ResultadoValidacaoEscopo(
            permitido=False,
            motivo=MotivoRecusa.FORA_DE_ESCOPO_ELETRICO,
            mensagem_usuario=(
                "Por segurança, não posso orientar instalação, reparo ou "
                "manuseio direto de equipamentos elétricos. Procure um "
                "eletricista certificado para esse tipo de intervenção."
            ),
        )

    return ResultadoValidacaoEscopo(permitido=True)


def contem_especificacao_nao_verificavel(texto_resposta: str, base_conhecimento: set[str]) -> bool:
    """
    Heurística simples para apoiar a checagem de "não inventar
    especificações de produtos não inseridas na base": procura por números
    seguidos de unidades técnicas (kW, kWh, V, A) na resposta do modelo que
    não aparecem em nenhum item da base de conhecimento fornecida.

    Isso é um apoio ao teste manual/eval, não um bloqueio automático —
    specs numéricas plausíveis não têm como ser 100% verificadas por regex.
    Use em conjunto com os casos de eval de "out-of-scope" (Etapa 3).
    """
    padrao_spec = re.compile(r"\b\d+(?:[.,]\d+)?\s*(kw|kwh|v|a)\b", re.IGNORECASE)
    specs_na_resposta = {m.group(0).lower() for m in padrao_spec.finditer(texto_resposta)}
    specs_na_base = {s.lower() for s in base_conhecimento}
    return not specs_na_resposta.issubset(specs_na_base) and bool(specs_na_resposta)
