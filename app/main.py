"""
Interface web — Streamlit (Aula 08 / §3 item 5 do enunciado).

Consome o pipeline RAG (src/rag/) e passa cada pergunta pelos guardrails
existentes (src/guardrails/) antes de chamar a chain, exibindo a resposta
com a(s) fonte(s) citada(s) de forma visível.

Inclui um modo opcional de comparação multi-provider (BÔNUS +1pt,
src/rag/multi_provider.py): mais de um modelo e mais de um prompt
consultados lado a lado para a mesma pergunta.

Uso:
    streamlit run app/main.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Streamlit, dependendo da versão/SO, só adiciona a pasta deste arquivo
# (app/) ao sys.path, não a raiz do projeto — o que quebra `from src...`
# mesmo rodando `streamlit run app/main.py` a partir da pasta certa.
# Inserir a raiz explicitamente resolve isso, mesmo padrão já usado em
# evals/run_eval_rag.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.guardrails.moderation import pipeline_guardrails
from src.rag.multi_provider import consultar_multi_provider_rag
from src.rag.rag_chain import build_rag_chain
from src.rag.retriever import build_retriever
from src.rag.vector_store import carregar_vector_store

# build_llm() (src/chain/builder.py) usa gpt-oss:120b como padrão — o
# modelo pedido pelo enunciado, mas não instalado nesta máquina. A
# interface usa llama3.1:8b como padrão real (mesmo já validado em
# docs/relatorio_modelos.md), sobrescrevível por EVCHALLENGE_MODEL.
MODELO_APP_PADRAO = os.environ.get("EVCHALLENGE_MODEL", "llama3.1:8b")

st.set_page_config(page_title="EV Challenge GoodWe — RAG", page_icon="🔌")
st.title("🔌 EV Challenge GoodWe — Assistente com RAG")
st.caption(
    "Sprint 04 — respostas baseadas na base de conhecimento (manuais, "
    "regimentos, FAQs e tabelas tarifárias). Toda resposta cita a fonte."
)


@st.cache_resource
def _carregar_retriever():
    vector_store = carregar_vector_store()
    return build_retriever(vector_store)


try:
    retriever = _carregar_retriever()
except FileNotFoundError as exc:
    st.error(
        f"{exc}\n\nRode `python -m src.rag.indexar` primeiro para indexar "
        "a base de conhecimento (data/knowledge_base/)."
    )
    st.stop()

modo_comparacao = st.sidebar.checkbox(
    "Comparar múltiplos modelos/prompts (bônus)",
    help="Consulta mais de um modelo e mais de um prompt RAG lado a lado para a mesma pergunta.",
)

pergunta = st.text_input("Pergunta sobre carregadores GoodWe:")


def _bloqueado(guardrail) -> bool:
    """pipeline_guardrails devolve ResultadoModeracao (.seguro) ou ResultadoValidacaoEscopo (.permitido)."""
    return not getattr(guardrail, "seguro", getattr(guardrail, "permitido", True))


def _exibir_resposta(resposta) -> None:
    st.markdown(resposta.resposta)
    if resposta.respondeu_com_contexto and resposta.fontes:
        st.markdown("**Fontes:**")
        for fonte in resposta.fontes:
            st.markdown(f"- {fonte}")
    elif not resposta.respondeu_com_contexto:
        st.info("Essa pergunta não foi respondida com base na base de conhecimento atual.")


if pergunta:
    guardrail = pipeline_guardrails(pergunta)
    if _bloqueado(guardrail):
        st.warning(guardrail.mensagem_usuario)
    elif modo_comparacao:
        with st.spinner("Consultando múltiplos modelos/prompts..."):
            resultado = consultar_multi_provider_rag(pergunta, retriever)

        for resposta in resultado.respostas:
            with st.expander(resposta.rotulo, expanded=True):
                if resposta.erro:
                    st.error(f"Erro: {resposta.erro}")
                else:
                    st.caption(f"Latência: {resposta.latencia_ms:.0f} ms")
                    _exibir_resposta(resposta.dados)
    else:
        with st.spinner("Consultando a base de conhecimento..."):
            chain = build_rag_chain(retriever, model=MODELO_APP_PADRAO)
            resposta = chain.invoke({"pergunta": pergunta})

        _exibir_resposta(resposta)
