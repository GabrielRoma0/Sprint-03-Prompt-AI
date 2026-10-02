"""
Embeddings — nomic-embed-text via Ollama (Aula 05 do Módulo 2).

Segue o mesmo padrão de `src/chain/builder.py`: override por variável de
ambiente, com um default fixo pedido pelo enunciado.
"""

from __future__ import annotations

import os

from langchain_ollama import OllamaEmbeddings

MODELO_EMBEDDING_PADRAO = "nomic-embed-text"


def build_embeddings(model: str | None = None) -> OllamaEmbeddings:
    """
    Instancia o modelo de embeddings local via Ollama.

    `model=None` usa `EVCHALLENGE_MODEL_EMBEDDING` se definida, senão
    `nomic-embed-text` (padrão do enunciado, §1).
    """
    if model is None:
        model = os.environ.get("EVCHALLENGE_MODEL_EMBEDDING", MODELO_EMBEDDING_PADRAO)
    return OllamaEmbeddings(model=model)
