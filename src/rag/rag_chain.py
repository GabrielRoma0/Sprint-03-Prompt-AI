"""
Chain RAG end-to-end — Sprint 04.

retriever -> formata contexto com fonte/página -> prompt_rag -> llm -> parser

Reaproveita `build_llm` da Sprint 03 (mesmo ChatOllama local) e os
guardrails de `src/guardrails/` (jailbreak/escopo) rodam antes desta chain
ser chamada, no mesmo padrão de `src/chain/guarded_chain.py`.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

from src.chain.builder import build_llm
from src.rag.prompt_rag import load_rag_prompt
from src.schemas.resposta_rag import RespostaRAG


def formatar_contexto(documentos: list[Document]) -> str:
    """
    Formata os chunks recuperados como texto único, um bloco por chunk,
    com a fonte (documento + página) explícita antes do conteúdo — é essa
    marcação que o prompt usa para preencher `fontes` na resposta.
    """
    blocos = []
    for doc in documentos:
        fonte = doc.metadata.get("source", "desconhecido")
        pagina = doc.metadata.get("page")
        cabecalho = f"[Fonte: {fonte}, p.{pagina + 1}]" if pagina is not None else f"[Fonte: {fonte}]"
        blocos.append(f"{cabecalho}\n{doc.page_content}")
    return "\n\n---\n\n".join(blocos)


def get_rag_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=RespostaRAG)


def build_rag_chain(
    retriever: BaseRetriever,
    model: str | None = None,
    temperature: float = 0.0,
    top_p: float = 0.9,
    prompt_version: str | None = None,
):
    """
    Monta a chain RAG completa.

    temperature=0.0 por padrão (diferente da chain conversacional da
    Sprint 03, que usa 0.2): RAG pede reprodutibilidade e aderência
    estrita ao contexto — ver docs/relatorio_modelos.md.
    """
    system_prompt = load_rag_prompt(prompt_version)
    parser = get_rag_parser()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            ("human", "CONTEXTO:\n{contexto}\n\nPERGUNTA: {pergunta}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    llm = build_llm(model=model, temperature=temperature, top_p=top_p)

    def _buscar_e_formatar(entrada: dict) -> dict:
        documentos = retriever.invoke(entrada["pergunta"])
        return {"pergunta": entrada["pergunta"], "contexto": formatar_contexto(documentos)}

    return _buscar_e_formatar | prompt | llm | parser


def responder(pergunta: str, retriever: BaseRetriever, **kwargs) -> RespostaRAG:
    """Atalho: monta a chain e responde uma única pergunta."""
    chain = build_rag_chain(retriever, **kwargs)
    return chain.invoke({"pergunta": pergunta})
