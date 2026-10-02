"""
Chunking da base de conhecimento com RecursiveCharacterTextSplitter.

Aula 05 do Módulo 2 (Sprint 04). Tamanho e overlap ficam centralizados
aqui para facilitar a comparação entre iterações — mudanças aqui devem
ser registradas em docs/relatorio_rag.md, com o efeito medido nos scores
de evals/.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Trade-off documentado em docs/relatorio_rag.md: chunks menores dão
# citação mais precisa (aponta o trecho exato) mas fragmentam contexto que
# se estende por parágrafos (ex.: uma tabela tarifária); chunks maiores
# preservam contexto mas citam um trecho mais genérico e usam mais tokens
# por chamada. 800/120 é o ponto de partida — ajustar conforme o eval.
TAMANHO_CHUNK = 800
OVERLAP_CHUNK = 120


def dividir_em_chunks(
    documentos: list[Document],
    tamanho: int = TAMANHO_CHUNK,
    overlap: int = OVERLAP_CHUNK,
) -> list[Document]:
    """Divide os Documents carregados em chunks menores, preservando metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamanho,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documentos)
