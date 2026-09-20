"""
Medição de tokens dos system prompts versionados (Aula 04 · Context Engineering).

Roda tiktoken sobre cada prompts/system_prompt_vN.md e imprime a contagem,
para alimentar a coluna "ganho medido" da tabela de versões
(prompts/versoes.md).

Uso:
    pip install tiktoken --break-system-packages   # se ainda não tiver
    python prompts/medir_tokens.py
"""

from __future__ import annotations

import glob
import os

import tiktoken

# cl100k_base é a codificação padrão usada como referência para medir
# prompts em projetos LangChain, independente do provedor final do LLM
# (gpt-oss:120b não expõe um tokenizer público próprio, então usamos essa
# codificação como proxy consistente entre versões).
ENCODING_NAME = "cl100k_base"


def contar_tokens(texto: str, encoding_name: str = ENCODING_NAME) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(texto))


def medir_todas_as_versoes(prompts_dir: str | None = None) -> dict[str, int]:
    if prompts_dir is None:
        prompts_dir = os.path.dirname(os.path.abspath(__file__))

    resultados: dict[str, int] = {}
    caminhos = sorted(glob.glob(os.path.join(prompts_dir, "system_prompt_v*.md")))

    for caminho in caminhos:
        versao = os.path.basename(caminho).replace("system_prompt_", "").replace(".md", "")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        resultados[versao] = contar_tokens(texto)

    return resultados


def main() -> None:
    resultados = medir_todas_as_versoes()
    if not resultados:
        print("Nenhum arquivo prompts/system_prompt_v*.md encontrado.")
        return

    print(f"Codificação usada: {ENCODING_NAME}\n")
    print(f"{'Versão':<10}{'Tokens':>10}")
    print("-" * 20)

    anterior = None
    for versao, tokens in resultados.items():
        print(f"{versao:<10}{tokens:>10}")
        if anterior is not None:
            delta = tokens - anterior
            sinal = "+" if delta >= 0 else ""
            print(f"  (variação vs. versão anterior: {sinal}{delta} tokens)")
        anterior = tokens


if __name__ == "__main__":
    main()
