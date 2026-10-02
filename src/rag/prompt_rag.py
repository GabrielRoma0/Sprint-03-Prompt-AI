"""
Prompt RAG versionado — carrega prompts/rag_prompt_{version}.md.

Segue o mesmo padrão de `src/chain/builder.py:load_system_prompt`, mas
para a família de prompts do pipeline RAG (Sprint 04). Cada versão nova
deve ser registrada em prompts/rag_versoes.md com o que mudou, por quê e
o score medido em evals/ (RAGAS ou fallback).
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

PROMPT_RAG_VERSAO_PADRAO = "v1"


def load_rag_prompt(version: str | None = None) -> str:
    """Carrega o system prompt RAG versionado de prompts/rag_prompt_{version}.md."""
    version = version or PROMPT_RAG_VERSAO_PADRAO
    path = PROMPTS_DIR / f"rag_prompt_{version}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt RAG '{version}' não encontrado em {path}. "
            "Crie o arquivo em prompts/ antes de montar a chain RAG."
        )
    return path.read_text(encoding="utf-8")
