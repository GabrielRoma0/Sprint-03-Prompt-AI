"""
Retriever — expõe a busca semântica configurada sobre o vector store.

Aula 05 do Módulo 2 (Sprint 04).
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever

TOP_K_PADRAO = 4


def build_retriever(vector_store: Chroma, k: int = TOP_K_PADRAO) -> BaseRetriever:
    """
    Retriever por similaridade, top-k configurável.

    k documentado em docs/relatorio_modelos.md junto de temperature/top_p —
    k maior dá mais contexto (e mais chance de grounding correto) às custas
    de mais tokens por chamada; k menor é mais barato mas arrisca faltar
    contexto relevante em perguntas que cruzam mais de um documento.
    """
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
