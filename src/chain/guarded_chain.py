"""
Integra os guardrails (moderação + escopo) à chain conversacional da
Etapa 1, formando o pipeline completo:

    entrada do usuário -> guardrails -> chain LCEL (com memória) -> saída

Se os guardrails barrarem a mensagem, a chain LCEL nem é chamada — evita
gasto de tokens com o LLM em mensagens já sabidamente fora de escopo ou
maliciosas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.chain.builder import get_parser
from src.guardrails.moderation import pipeline_guardrails
from src.schemas.consulta_recarga import ConsultaRecarga


@dataclass
class RespostaChatbot:
    bloqueado: bool
    mensagem: str
    dados: ConsultaRecarga | None = None


def invocar_com_guardrails(
    conversational_chain: Any,
    texto_usuario: str,
    session_id: str,
) -> RespostaChatbot:
    """
    Ponto de entrada único do chatbot: roda os guardrails antes de tocar
    na chain LCEL/LLM.

    `conversational_chain` deve ser a chain SEM o parser embutido (ver
    `build_chain(..., with_parser=False)` + `build_conversational_chain`),
    porque `RunnableWithMessageHistory` só consegue persistir a saída no
    histórico quando ela é uma `AIMessage`/string — o parsing para
    `ConsultaRecarga` acontece aqui, depois que a memória já foi atualizada.
    """
    resultado_guardrail = pipeline_guardrails(texto_usuario)

    # ResultadoModeracao usa `seguro`; ResultadoValidacaoEscopo usa `permitido`.
    # pipeline_guardrails pode retornar qualquer um dos dois, então checamos
    # o atributo disponível.
    passou = getattr(resultado_guardrail, "seguro", None)
    if passou is None:
        passou = resultado_guardrail.permitido

    if not passou:
        return RespostaChatbot(bloqueado=True, mensagem=resultado_guardrail.mensagem_usuario)

    resposta_llm = conversational_chain.invoke(
        {"input": texto_usuario},
        config={"configurable": {"session_id": session_id}},
    )
    dados: ConsultaRecarga = get_parser().invoke(resposta_llm)
    return RespostaChatbot(bloqueado=False, mensagem="ok", dados=dados)
