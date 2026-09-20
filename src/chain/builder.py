"""
Chain LCEL end-to-end — reconstrução do núcleo conversacional do chatbot
EV Challenge GoodWe usando LangChain (Aula 01 do Módulo 1).

chain = ChatPromptTemplate | ChatOllama | PydanticOutputParser
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from src.schemas.consulta_recarga import ConsultaRecarga

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_system_prompt(version: str = "v1") -> str:
    """Carrega o system prompt versionado de prompts/system_prompt_{version}.md."""
    path = PROMPTS_DIR / f"system_prompt_{version}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt '{version}' não encontrado em {path}. "
            "Crie o arquivo em prompts/ antes de construir a chain."
        )
    return path.read_text(encoding="utf-8")


MODELO_PADRAO = "gpt-oss:120b"  # modelo pedido pelo enunciado (§3, item 1)
PROMPT_VERSAO_PADRAO = "v3"  # versão mais recente — ver prompts/versoes.md


def build_llm(model: str | None = None, temperature: float = 0.2, top_p: float = 0.9) -> ChatOllama:
    """
    Instancia o modelo local via Ollama.

    `model=None` usa `EVCHALLENGE_MODEL` (variável de ambiente) se definida,
    senão o padrão do enunciado (`gpt-oss:120b`). Isso permite rodar os
    demos/eval em máquinas onde o modelo de 120B ainda não foi baixado, sem
    mudar o comportamento padrão esperado pela rubrica.

    Os parâmetros (temperature, top_p) devem ser documentados em
    docs/relatorio_modelos.md (Etapa 3).
    """
    if model is None:
        model = os.environ.get("EVCHALLENGE_MODEL", MODELO_PADRAO)
    # format="json" força o modo JSON nativo do Ollama: sem isso, modelos
    # menores (ex.: llama3.1:8b) às vezes respondem com texto livre em vez
    # do schema pedido (ex.: recusando um valor de potência negativo em
    # prosa) e o PydanticOutputParser falha com "Invalid json output" — ver
    # "Problemas encontrados" em docs/relatorio_evolucao.pdf.
    return ChatOllama(model=model, temperature=temperature, top_p=top_p, format="json")


def get_parser() -> PydanticOutputParser:
    """Parser Pydantic v2 compartilhado (schema ConsultaRecarga, Aula 03)."""
    return PydanticOutputParser(pydantic_object=ConsultaRecarga)


def build_chain(
    model: str | None = None,
    temperature: float = 0.2,
    top_p: float = 0.9,
    prompt_version: str | None = None,
    with_parser: bool = True,
):
    """
    Monta a chain LCEL: prompt | llm | parser.

    A saída é sempre validada pelo schema Pydantic v2 `ConsultaRecarga`
    (Aula 03).

    `with_parser=False` retorna só `prompt | llm` (saída = AIMessage), usado
    por `src/chain/memoria.py`: `RunnableWithMessageHistory` só sabe
    persistir texto/`BaseMessage` no histórico, não um objeto Pydantic
    arbitrário, então a memória por sessão envolve a chain SEM o parser e
    quem chama aplica `get_parser()` no `.content` da resposta depois do
    `.invoke()` (ver `src/chain/guarded_chain.py`).
    """
    system_prompt = load_system_prompt(prompt_version or PROMPT_VERSAO_PADRAO)
    parser = get_parser()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt + "\n\n{format_instructions}"),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    llm = build_llm(model=model, temperature=temperature, top_p=top_p)

    chain = prompt | llm
    if with_parser:
        chain = chain | parser
    return chain
