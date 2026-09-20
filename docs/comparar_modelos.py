"""
Comparação de 2+ modelos com os mesmos parâmetros (Bloco B da rubrica).

Roda os casos happy_path/edge_case de evals/eval_set.json contra dois
modelos Ollama e grava docs/comparacao_modelos_resultado.json com taxa de
acerto e latência de cada um, para preencher a tabela de
docs/relatorio_modelos.md.

Uso:
    python docs/comparar_modelos.py
    EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python docs/comparar_modelos.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chain.builder import build_chain, build_llm  # noqa: E402
from src.chain.guarded_chain import invocar_com_guardrails  # noqa: E402
from src.chain.memoria import build_conversational_chain  # noqa: E402
from evals.run_eval import _checar_criterio  # noqa: E402

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "evals" / "eval_set.json"
RESULT_PATH = Path(__file__).resolve().parent / "comparacao_modelos_resultado.json"

MODELO_PRIMARIO = os.environ.get("EVCHALLENGE_MODEL", "llama3.1:8b")
MODELO_SECUNDARIO = os.environ.get("EVCHALLENGE_MODEL_SECUNDARIO", "gemma2:2b")
TEMPERATURE = 0.2
TOP_P = 0.9


def rodar_modelo(modelo: str, casos: list[dict]) -> dict:
    llm = build_llm(model=modelo, temperature=TEMPERATURE, top_p=TOP_P)
    chain = build_conversational_chain(
        build_chain(model=modelo, temperature=TEMPERATURE, top_p=TOP_P, with_parser=False),
        llm,
        max_token_limit=800,
    )

    resultados = []
    for caso in casos:
        inicio = time.perf_counter()
        try:
            resposta = invocar_com_guardrails(chain, caso["entrada"], session_id=f"cmp-{modelo}-{caso['id']}")
            latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
            dados = resposta.dados.model_dump(mode="json") if resposta.dados else None
            erro = None
        except Exception as exc:  # noqa: BLE001
            latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
            dados = None
            erro = str(exc)

        passou = _checar_criterio(caso, dados) if erro is None else False
        resultados.append(
            {"id": caso["id"], "passou": passou, "latencia_ms": latencia_ms, "dados": dados, "erro": erro}
        )

    avaliados = [r for r in resultados if r["passou"] is not None]
    aprovados = sum(1 for r in avaliados if r["passou"])
    latencia_media = round(sum(r["latencia_ms"] for r in resultados) / len(resultados), 2)

    return {
        "modelo": modelo,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "casos_avaliaveis_automaticamente": len(avaliados),
        "aprovados": aprovados,
        "taxa_acerto": f"{aprovados}/{len(avaliados)}" if avaliados else "N/A",
        "latencia_media_ms": latencia_media,
        "resultados": resultados,
    }


def main() -> None:
    eval_set = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    casos_llm = [c for c in eval_set["casos"] if c["categoria"] in ("happy_path", "edge_case")]

    saida = {"casos_testados": [c["id"] for c in casos_llm], "modelos": []}
    for modelo in (MODELO_PRIMARIO, MODELO_SECUNDARIO):
        print(f"Rodando {len(casos_llm)} casos com {modelo}...")
        saida["modelos"].append(rodar_modelo(modelo, casos_llm))

    RESULT_PATH.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultado gravado em {RESULT_PATH}\n")
    for m in saida["modelos"]:
        print(f"{m['modelo']}: taxa_acerto={m['taxa_acerto']} latencia_media_ms={m['latencia_media_ms']}")


if __name__ == "__main__":
    main()
