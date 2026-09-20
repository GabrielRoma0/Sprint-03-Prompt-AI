"""
Demonstração da Etapa 1: chain LCEL + memória por sessão + structured output.

Executa 3+ turnos de conversa na mesma sessão para provar que a memória
está funcionando, e imprime a saída validada pelo schema ConsultaRecarga
a cada turno.

Requer Ollama rodando localmente com o modelo `gpt-oss:120b` disponível:
    ollama pull gpt-oss:120b
    ollama serve

Rodar a partir da raiz do projeto:
    python demo_etapa1.py
"""

from __future__ import annotations

from src.chain.builder import build_chain, build_llm
from src.chain.guarded_chain import invocar_com_guardrails
from src.chain.memoria import build_conversational_chain, get_session_history

SESSION_ID = "demo-sessao-01"

TURNOS = [
    "O carregador CP-104 está em carga, entregando 7.4 kW no momento.",
    "Até agora ele já entregou 12.5 kWh nessa sessão.",
    "O valor faturado até agora foi de 18.90 reais.",
    "Na verdade a carga acabou de concluir, pode atualizar o estado?",
]


def main() -> None:
    llm = build_llm()
    # with_parser=False: RunnableWithMessageHistory precisa que a saída da
    # chain seja uma AIMessage para conseguir persistir no histórico; o
    # parsing para ConsultaRecarga acontece dentro de invocar_com_guardrails.
    base_chain = build_chain(with_parser=False)
    conversational_chain = build_conversational_chain(base_chain, llm, max_token_limit=800)

    for i, turno in enumerate(TURNOS, start=1):
        print(f"\n=== Turno {i} ===")
        print(f"Usuário: {turno}")
        resposta = invocar_com_guardrails(conversational_chain, turno, session_id=SESSION_ID)
        print(f"Saída estruturada (ConsultaRecarga): {resposta.dados.model_dump()}")

    historico = get_session_history(SESSION_ID, llm)
    print(f"\n=== Prova de memória: {len(historico.messages)} mensagens retidas na sessão ===")
    for msg in historico.messages:
        print(f"  {type(msg).__name__}: {msg.content[:100]}")


if __name__ == "__main__":
    main()
