"""
Demonstração do BÔNUS (+1 pt): chamada multi-provider.

Consulta a mesma entrada do usuário contra 3 combinações de (modelo,
versão de prompt) e imprime as respostas lado a lado.

Requer Ollama local com os modelos usados em CONFIGURACOES_PADRAO
(gpt-oss:120b e qwen3:8b):
    ollama pull gpt-oss:120b
    ollama pull qwen3:8b

Rodar a partir da raiz do projeto:
    python demo_bonus_multiprovider.py
"""

from __future__ import annotations

from src.chain.multi_provider import consultar_multi_provider

ENTRADA = "O carregador CP-104 está em carga, entregando 7.4 kW no momento."


def main() -> None:
    resultado = consultar_multi_provider(ENTRADA, session_id="demo-bonus")

    if resultado.bloqueado_por_guardrail:
        print(f"Bloqueado pelo guardrail: {resultado.mensagem_guardrail}")
        return

    print(f"Entrada: {resultado.entrada}\n")
    for resposta in resultado.respostas:
        print(f"--- {resposta.rotulo} ---")
        if resposta.erro:
            print(f"  Erro: {resposta.erro}")
        else:
            print(f"  Latência: {resposta.latencia_ms} ms")
            print(f"  Saída: {resposta.dados.model_dump()}")
        print()


if __name__ == "__main__":
    main()
