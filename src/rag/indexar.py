"""
Script de indexação — roda o pipeline loader -> chunking -> auditoria ->
vector store uma única vez, populando data/chroma_db/.

Uso:
    python -m src.rag.indexar
"""

from __future__ import annotations

from src.guardrails.document_sanitizer import auditar_chunks
from src.rag.chunking import dividir_em_chunks
from src.rag.loader import carregar_documentos
from src.rag.vector_store import construir_vector_store


def main() -> None:
    print("Carregando PDFs de data/knowledge_base/...")
    documentos = carregar_documentos()
    print(f"  {len(documentos)} páginas carregadas.")

    print("Dividindo em chunks...")
    chunks = dividir_em_chunks(documentos)
    print(f"  {len(chunks)} chunks gerados.")

    print("Auditando chunks (prompt injection via documento)...")
    suspeitos = auditar_chunks(chunks)
    if suspeitos:
        print(f"  {len(suspeitos)} chunk(s) sinalizado(s) — revisar antes da entrega:")
        for s in suspeitos:
            print(f"    - {s.source} (p.{s.page}): {s.trecho!r}")
    else:
        print("  Nenhum chunk suspeito encontrado.")

    print("Indexando no ChromaDB (nomic-embed-text)...")
    construir_vector_store(chunks)
    print("Concluído. Vector store persistido em data/chroma_db/.")


if __name__ == "__main__":
    main()
