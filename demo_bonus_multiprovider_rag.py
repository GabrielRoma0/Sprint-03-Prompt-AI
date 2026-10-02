"""
Demonstração do BÔNUS (+1 pt) no pipeline RAG: chamada multi-provider.

Consulta a mesma pergunta contra 3 combinações de (modelo, versão do
prompt RAG) e imprime as respostas lado a lado, com fonte citada por
combinação.

Requer:
- Ollama local com nomic-embed-text e os modelos de
  src/rag/multi_provider.py:CONFIGURACOES_PADRAO_RAG (llama3.1:8b,
  gemma2:2b por padrão — sobrescrevíveis por EVCHALLENGE_MODEL/
  EVCHALLENGE_MODEL_SECUNDARIO).
- Base já indexada: rodar `python -m src.rag.indexar` antes, se ainda não
  tiver rodado.

Rodar a partir da raiz do projeto:
    python demo_bonus_multiprovider_rag.py
"""

from __future__ import annotations

from src.rag.multi_provider import consultar_multi_provider_rag
from src.rag.retriever import build_retriever
from src.rag.vector_store import carregar_vector_store

PERGUNTA = "Qual a potência máxima suportada pelo carregador GoodWe ChargeGrid em modo trifásico?"


def main() -> None:
    vector_store = carregar_vector_store()
    retriever = build_retriever(vector_store)

    resultado = consultar_multi_provider_rag(PERGUNTA, retriever)

    if resultado.bloqueado_por_guardrail:
        print(f"Bloqueado pelo guardrail: {resultado.mensagem_guardrail}")
        return

    print(f"Pergunta: {resultado.pergunta}\n")
    for resposta in resultado.respostas:
        print(f"--- {resposta.rotulo} ---")
        if resposta.erro:
            print(f"  Erro: {resposta.erro}")
        else:
            print(f"  Latência: {resposta.latencia_ms} ms")
            print(f"  respondeu_com_contexto: {resposta.dados.respondeu_com_contexto}")
            print(f"  fontes: {resposta.dados.fontes}")
            print(f"  resposta: {resposta.dados.resposta}")
        print()


if __name__ == "__main__":
    main()
