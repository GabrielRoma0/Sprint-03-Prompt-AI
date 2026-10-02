"""
Loader da base de conhecimento — carrega os PDFs de data/knowledge_base/
e devolve Documents do LangChain com metadata de origem preservada.

Aula 05 do Módulo 2 (Sprint 04).
"""

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge_base"


def carregar_documentos(diretorio: Path | None = None) -> list[Document]:
    """
    Carrega todos os PDFs de `diretorio` (padrão: data/knowledge_base/).

    Cada Document sai com `metadata["source"]` = nome do arquivo e
    `metadata["page"]` = número da página — usados depois para a citação
    de fonte exigida pelo enunciado (§3, item 3).
    """
    diretorio = diretorio or DATA_DIR
    if not diretorio.exists():
        raise FileNotFoundError(
            f"Pasta de base de conhecimento não encontrada: {diretorio}. "
            "Adicione os PDFs do domínio (manuais GoodWe, regimentos, FAQs, "
            "tabelas tarifárias) antes de indexar."
        )

    pdfs = sorted(diretorio.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"Nenhum PDF encontrado em {diretorio}. "
            "A base de conhecimento precisa de pelo menos um documento."
        )

    documentos: list[Document] = []
    for pdf_path in pdfs:
        loader = PyMuPDFLoader(str(pdf_path))
        paginas = loader.load()
        # PyMuPDFLoader já preenche metadata["source"] com o caminho completo;
        # normalizamos para só o nome do arquivo, mais legível na citação.
        for doc in paginas:
            doc.metadata["source"] = pdf_path.name
        documentos.extend(paginas)

    return documentos
