"""
Vector store — ChromaDB persistente (Aula 05 do Módulo 2).

Indexa os chunks da base de conhecimento e permite recarregar a coleção
já indexada sem reprocessar os PDFs a cada execução.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.embeddings import build_embeddings

PERSIST_DIR = Path(__file__).resolve().parents[2] / "data" / "chroma_db"
NOME_COLECAO = "goodwe_ev_knowledge_base"


def construir_vector_store(chunks: list[Document], persist_dir: Path | None = None) -> Chroma:
    """
    Cria (ou recria) a coleção Chroma a partir dos chunks fornecidos,
    persistindo em disco para não precisar reindexar a cada execução.
    """
    persist_dir = persist_dir or PERSIST_DIR
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma.from_documents(
        documents=chunks,
        embedding=build_embeddings(),
        collection_name=NOME_COLECAO,
        persist_directory=str(persist_dir),
    )


def carregar_vector_store(persist_dir: Path | None = None) -> Chroma:
    """
    Abre a coleção já indexada em disco, sem reprocessar os documentos.

    Usar depois que `construir_vector_store` já rodou pelo menos uma vez
    (ex.: em `app/main.py`, para não reindexar a cada request).
    """
    persist_dir = persist_dir or PERSIST_DIR
    if not persist_dir.exists():
        raise FileNotFoundError(
            f"Vector store não encontrado em {persist_dir}. "
            "Rode a indexação primeiro (ver src/rag/vector_store.py:construir_vector_store)."
        )

    return Chroma(
        collection_name=NOME_COLECAO,
        embedding_function=build_embeddings(),
        persist_directory=str(persist_dir),
    )
