"""
BÔNUS (+1 pt) — chamada multi-provider.

Consulta mais de um modelo E mais de um prompt para a mesma entrada do
usuário, retornando as respostas lado a lado. Útil tanto como recurso do
produto (comparar respostas antes de decidir qual confiar) quanto como
ferramenta de avaliação (mesma base do relatório de modelos, Etapa 3).

Não substitui a chain principal (src/chain/builder.py + memoria.py) — é um
modo de consulta adicional que roda N combinações (modelo, versão de
prompt) em paralelo lógico e agrega os resultados.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from time import perf_counter

from src.chain.builder import build_chain, build_llm, get_parser
from src.chain.memoria import build_conversational_chain
from src.guardrails.moderation import pipeline_guardrails
from src.schemas.consulta_recarga import ConsultaRecarga


@dataclass
class ConfiguracaoProvider:
    """Uma combinação (modelo, versão de prompt, parâmetros) a consultar."""

    model: str
    prompt_version: str
    temperature: float = 0.2
    top_p: float = 0.9
    rotulo: str | None = None  # nome amigável para exibir nos resultados

    def __post_init__(self):
        if self.rotulo is None:
            self.rotulo = f"{self.model} · prompt {self.prompt_version}"


@dataclass
class RespostaProvider:
    rotulo: str
    model: str
    prompt_version: str
    dados: ConsultaRecarga | None
    erro: str | None
    latencia_ms: float


@dataclass
class RespostaMultiProvider:
    entrada: str
    bloqueado_por_guardrail: bool
    mensagem_guardrail: str | None
    respostas: list[RespostaProvider] = field(default_factory=list)


# Modelos pedidos pelo enunciado (§3, item 1 + relatório de modelos). Podem
# ser sobrescritos por EVCHALLENGE_MODEL / EVCHALLENGE_MODEL_SECUNDARIO em
# máquinas onde gpt-oss:120b/qwen3:8b ainda não foram baixados — ver
# docs/relatorio_modelos.md para a justificativa da substituição usada.
_MODELO_PRIMARIO = os.environ.get("EVCHALLENGE_MODEL", "gpt-oss:120b")
_MODELO_SECUNDARIO = os.environ.get("EVCHALLENGE_MODEL_SECUNDARIO", "qwen3:8b")

# Configuração padrão do bônus: 2 modelos x 1 prompt cada = 2 combinações,
# já satisfaz "mais de um modelo e mais de um prompt" combinando
# diferentes prompts por modelo. Ajuste livremente.
CONFIGURACOES_PADRAO = [
    ConfiguracaoProvider(model=_MODELO_PRIMARIO, prompt_version="v3"),
    ConfiguracaoProvider(model=_MODELO_PRIMARIO, prompt_version="v1"),
    ConfiguracaoProvider(model=_MODELO_SECUNDARIO, prompt_version="v3"),
]


def consultar_multi_provider(
    texto_usuario: str,
    session_id: str,
    configuracoes: list[ConfiguracaoProvider] | None = None,
) -> RespostaMultiProvider:
    """
    Roda os guardrails uma única vez (o resultado vale para todas as
    combinações) e, se a mensagem passar, consulta cada combinação de
    (modelo, prompt) da lista `configuracoes`.

    Cada combinação usa uma session_id própria (`{session_id}::{rotulo}`)
    para não misturar o histórico de memória entre modelos/prompts
    diferentes.
    """
    if configuracoes is None:
        configuracoes = CONFIGURACOES_PADRAO

    resultado_guardrail = pipeline_guardrails(texto_usuario)
    passou = getattr(resultado_guardrail, "seguro", None)
    if passou is None:
        passou = resultado_guardrail.permitido

    if not passou:
        return RespostaMultiProvider(
            entrada=texto_usuario,
            bloqueado_por_guardrail=True,
            mensagem_guardrail=resultado_guardrail.mensagem_usuario,
        )

    respostas: list[RespostaProvider] = []
    for config in configuracoes:
        inicio = perf_counter()
        try:
            llm = build_llm(model=config.model, temperature=config.temperature, top_p=config.top_p)
            chain = build_conversational_chain(
                build_chain(
                    model=config.model,
                    temperature=config.temperature,
                    prompt_version=config.prompt_version,
                    with_parser=False,
                ),
                llm,
            )
            resposta_llm = chain.invoke(
                {"input": texto_usuario},
                config={"configurable": {"session_id": f"{session_id}::{config.rotulo}"}},
            )
            dados = get_parser().invoke(resposta_llm)
            erro = None
        except Exception as exc:  # noqa: BLE001 — queremos capturar qualquer falha de provider individual
            dados = None
            erro = str(exc)

        latencia_ms = round((perf_counter() - inicio) * 1000, 2)
        respostas.append(
            RespostaProvider(
                rotulo=config.rotulo,
                model=config.model,
                prompt_version=config.prompt_version,
                dados=dados,
                erro=erro,
                latencia_ms=latencia_ms,
            )
        )

    return RespostaMultiProvider(
        entrada=texto_usuario,
        bloqueado_por_guardrail=False,
        mensagem_guardrail=None,
        respostas=respostas,
    )
