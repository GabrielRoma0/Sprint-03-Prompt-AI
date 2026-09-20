"""
Memória conversacional por sessão, com limite de tokens (Aula 02 do Módulo 1).

Combina:
  - ConversationTokenBufferMemory: motor de armazenamento do histórico da
    sessão; a poda por `max_token_limit` é reimplementada aqui com tiktoken
    (ver `_contar_tokens_mensagens`) em vez do `get_num_tokens_from_messages`
    do LLM, que exigiria o pacote `transformers` para o ChatOllama.
  - RunnableWithMessageHistory: injeta/atualiza esse histórico
    automaticamente a cada turno da chain LCEL.
"""

from __future__ import annotations

import tiktoken

try:
    # langchain >= 1.0 moveu ConversationTokenBufferMemory para o pacote
    # de compatibilidade langchain-classic; langchain 0.3.x ainda tem em
    # langchain.memory diretamente. Tentamos os dois caminhos para que o
    # código rode em qualquer uma das duas versões suportadas pela Aula 02.
    from langchain.memory import ConversationTokenBufferMemory
except ModuleNotFoundError:
    from langchain_classic.memory import ConversationTokenBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, get_buffer_string
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

# ChatOllama não implementa get_num_tokens_from_messages de forma nativa —
# o fallback genérico do LangChain precisa do pacote `transformers` (GPT-2
# tokenizer), que não é uma dependência deste projeto. Usamos tiktoken
# (cl100k_base) como proxy de contagem para a poda, igual a
# prompts/medir_tokens.py, em vez de `llm.get_num_tokens_from_messages`.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def _contar_tokens_mensagens(mensagens: list[BaseMessage]) -> int:
    return len(_ENCODING.encode(get_buffer_string(mensagens)))

# Armazém em memória de processo: {session_id: TokenLimitedHistory}
# Em produção isso poderia ser trocado por Redis/SQLite sem mudar a
# assinatura de get_session_history.
_session_store: dict[str, "TokenLimitedHistory"] = {}


class TokenLimitedHistory(BaseChatMessageHistory):
    """
    Histórico de chat por sessão que se auto-poda por limite de tokens,
    usando ConversationTokenBufferMemory como motor de contagem/poda.
    """

    def __init__(self, session_id: str, llm: ChatOllama, max_token_limit: int = 1000):
        self.session_id = session_id
        self.max_token_limit = max_token_limit
        self._memory = ConversationTokenBufferMemory(
            llm=llm,
            max_token_limit=max_token_limit,
            return_messages=True,
        )

    @property
    def messages(self) -> list[BaseMessage]:
        return self._memory.chat_memory.messages

    def add_message(self, message: BaseMessage) -> None:
        self._memory.chat_memory.add_message(message)
        # ConversationTokenBufferMemory faz essa poda dentro de
        # save_context() (não expõe um `.prune()` público nesta versão do
        # langchain) — reproduzimos aqui o mesmo algoritmo: remove as
        # mensagens mais antigas até a contagem de tokens caber em
        # max_token_limit (contagem via tiktoken, ver comentário no topo
        # do módulo sobre por que não usamos llm.get_num_tokens_from_messages).
        buffer = self._memory.chat_memory.messages
        while _contar_tokens_mensagens(buffer) > self.max_token_limit and buffer:
            buffer.pop(0)

    def clear(self) -> None:
        self._memory.chat_memory.clear()


def get_session_history(session_id: str, llm: ChatOllama, max_token_limit: int = 1000) -> TokenLimitedHistory:
    """Recupera (ou cria) o histórico com limite de tokens de uma sessão."""
    if session_id not in _session_store:
        _session_store[session_id] = TokenLimitedHistory(session_id, llm, max_token_limit)
    return _session_store[session_id]


def build_conversational_chain(chain, llm: ChatOllama, max_token_limit: int = 1000):
    """
    Envolve a chain LCEL (prompt | llm | parser) com memória por sessão.

    Uso:
        resposta = conversational_chain.invoke(
            {"input": "..."},
            config={"configurable": {"session_id": "usuario-123"}},
        )
    """
    return RunnableWithMessageHistory(
        chain,
        lambda session_id: get_session_history(session_id, llm, max_token_limit),
        input_messages_key="input",
        history_messages_key="history",
    )
