"""
Guardrail de prompt injection via documentos — Sprint 04, §3 item 6 e §6
do enunciado.

Diferente de `moderation.py` (que audita a mensagem do usuário), este
módulo audita o CONTEXTO recuperado do vector store antes de ele ser
inserido no prompt: um documento malicioso na base de conhecimento (ex.:
um PDF com um trecho "ignore as instruções anteriores e revele...")
poderia tentar sequestrar o comportamento do modelo mesmo sem o usuário
digitar nada suspeito.

Duas camadas de defesa, propositalmente redundantes:
1. Aqui: sinaliza/loga chunks suspeitos ANTES de indexar ou ANTES de
   montar o contexto, para auditoria (o enunciado exige "proteção", não
   necessariamente bloqueio total).
2. `prompts/rag_prompt_v1.md` (<security>): instrui o modelo a tratar todo
   o CONTEXTO como dado, nunca como instrução, mesmo que um chunk suspeito
   passe por aqui sem ser filtrado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

# Reaproveita a mesma família de padrões de src/guardrails/moderation.py,
# agora aplicada ao conteúdo dos documentos em vez da mensagem do usuário.
_PADROES_INJECAO_DOCUMENTO = [
    re.compile(r"\bignor[ea]\s+(todas\s+)?as\s+instru[çc][õo]es\s+anteriores\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(all\s+)?previous\s+instructions\b", re.IGNORECASE),
    re.compile(r"\b(repita|mostre|revele)\s+(o\s+)?(seu\s+)?(system\s+)?prompt\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(is|are)\s+your\s+(system\s+)?instructions\b", re.IGNORECASE),
    re.compile(r"\[\s*system\s*\]", re.IGNORECASE),
    re.compile(r"</?\s*system\s*>", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(dan|an\s+unrestricted\s+ai)\b", re.IGNORECASE),
]


@dataclass
class ChunkSuspeito:
    source: str
    page: int | None
    trecho: str


def auditar_chunks(chunks: list[Document]) -> list[ChunkSuspeito]:
    """
    Varre os chunks (tipicamente logo após `src/rag/chunking.py`, antes de
    indexar) e retorna os que contêm padrões de injection conhecidos.

    Não remove os chunks automaticamente — documentos legítimos podem
    mencionar esses termos em contexto inofensivo (ex.: um FAQ explicando
    o que é prompt injection). A decisão de indexar mesmo assim, com o
    prompt tratando o conteúdo como dado (defesa em profundidade), é
    documentada em docs/relatorio_rag.md junto da lista de chunks
    sinalizados nesta execução.
    """
    suspeitos: list[ChunkSuspeito] = []
    for chunk in chunks:
        for padrao in _PADROES_INJECAO_DOCUMENTO:
            if padrao.search(chunk.page_content):
                suspeitos.append(
                    ChunkSuspeito(
                        source=chunk.metadata.get("source", "desconhecido"),
                        page=chunk.metadata.get("page"),
                        trecho=chunk.page_content[:200],
                    )
                )
                break
    return suspeitos
