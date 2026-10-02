"""
BÔNUS (+1 pt) — chamada multi-provider no pipeline RAG.

Mesmo conceito do bônus da Sprint 03 (src/chain/multi_provider.py), agora
aplicado ao RAG: consulta mais de um modelo E mais de um prompt RAG para a
mesma pergunta, contra o mesmo retriever/contexto recuperado, retornando
as respostas lado a lado com fonte citada por combinação.

Não substitui `src/rag/rag_chain.py` — é um modo de consulta adicional
que roda N combinações (modelo, versão de prompt RAG) e agrega os
resultados. Útil tanto como recurso do produto (comparar respostas antes
de confiar) quanto como ferramenta de avaliação (mesma base usada em
docs/relatorio_modelos.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from time import perf_counter

from langchain_core.retrievers import BaseRetriever

from src.guardrails.moderation import pipeline_guardrails
from src.rag.rag_chain import build_rag_chain
from src.schemas.resposta_rag import RespostaRAG


@dataclass
class ConfiguracaoProviderRAG:
    """Uma combinação (modelo, versão do prompt RAG, parâmetros) a consultar."""

    model: str
    prompt_version: str
    temperature: float = 0.0
    top_p: float = 0.9
    rotulo: str | None = None

    def __post_init__(self):
        if self.rotulo is None:
            self.rotulo = f"{self.model} · prompt {self.prompt_version}"


@dataclass
class RespostaProviderRAG:
    rotulo: str
    model: str
    prompt_version: str
    dados: RespostaRAG | None
    erro: str | None
    latencia_ms: float


@dataclass
class RespostaMultiProviderRAG:
    pergunta: str
    bloqueado_por_guardrail: bool
    mensagem_guardrail: str | None
    respostas: list[RespostaProviderRAG] = field(default_factory=list)


# Modelos já validados nesta entrega (ver docs/relatorio_modelos.md, seção
# Sprint 04) — llama3.1:8b é o principal (faithfulness 1.0 nas 2
# iterações), gemma2:2b o secundário de comparação. Sobrescrevíveis por
# variável de ambiente, mesmo padrão do bônus da Sprint 03.
_MODELO_PRIMARIO = os.environ.get("EVCHALLENGE_MODEL", "llama3.1:8b")
_MODELO_SECUNDARIO = os.environ.get("EVCHALLENGE_MODEL_SECUNDARIO", "gemma2:2b")

# Configuração padrão: 2 modelos x prompts diferentes = 3 combinações,
# satisfaz "mais de um modelo e mais de um prompt" (§6 do enunciado).
CONFIGURACOES_PADRAO_RAG = [
    ConfiguracaoProviderRAG(model=_MODELO_PRIMARIO, prompt_version="v2"),
    ConfiguracaoProviderRAG(model=_MODELO_PRIMARIO, prompt_version="v1"),
    ConfiguracaoProviderRAG(model=_MODELO_SECUNDARIO, prompt_version="v2"),
]


def consultar_multi_provider_rag(
    pergunta: str,
    retriever: BaseRetriever,
    configuracoes: list[ConfiguracaoProviderRAG] | None = None,
) -> RespostaMultiProviderRAG:
    """
    Roda os guardrails uma única vez (vale para todas as combinações) e,
    se a pergunta passar, consulta cada combinação de (modelo, prompt RAG)
    da lista `configuracoes` contra o mesmo `retriever`.
    """
    if configuracoes is None:
        configuracoes = CONFIGURACOES_PADRAO_RAG

    resultado_guardrail = pipeline_guardrails(pergunta)
    passou = getattr(resultado_guardrail, "seguro", None)
    if passou is None:
        passou = resultado_guardrail.permitido

    if not passou:
        return RespostaMultiProviderRAG(
            pergunta=pergunta,
            bloqueado_por_guardrail=True,
            mensagem_guardrail=resultado_guardrail.mensagem_usuario,
        )

    respostas: list[RespostaProviderRAG] = []
    for config in configuracoes:
        inicio = perf_counter()
        try:
            chain = build_rag_chain(
                retriever,
                model=config.model,
                temperature=config.temperature,
                top_p=config.top_p,
                prompt_version=config.prompt_version,
            )
            dados = chain.invoke({"pergunta": pergunta})
            erro = None
        except Exception as exc:  # noqa: BLE001 — 1 provider falhar não deve derrubar os demais
            dados = None
            erro = str(exc)

        latencia_ms = round((perf_counter() - inicio) * 1000, 2)
        respostas.append(
            RespostaProviderRAG(
                rotulo=config.rotulo,
                model=config.model,
                prompt_version=config.prompt_version,
                dados=dados,
                erro=erro,
                latencia_ms=latencia_ms,
            )
        )

    return RespostaMultiProviderRAG(
        pergunta=pergunta,
        bloqueado_por_guardrail=False,
        mensagem_guardrail=None,
        respostas=respostas,
    )
