"""
Reexecuta evals/eval_set.json sobre a versão refatorada (LCEL + memória +
guardrails) e grava evals/sprint3_results.json.

- Casos "jailbreak" e "out_of_scope" rodam só contra os guardrails
  (src/guardrails), sem precisar do Ollama.
- Casos "happy_path" e "edge_case" precisam da chain completa
  (src/chain/guarded_chain.py) e, portanto, do Ollama rodando localmente
  com o modelo configurado.

Uso:
    python evals/run_eval.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Permite rodar tanto com `python evals/run_eval.py` quanto com
# `python -m evals.run_eval` a partir da raiz do projeto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chain.builder import build_chain, build_llm  # noqa: E402
from src.chain.guarded_chain import invocar_com_guardrails  # noqa: E402
from src.chain.memoria import build_conversational_chain  # noqa: E402
from src.guardrails.moderation import pipeline_guardrails  # noqa: E402

EVAL_SET_PATH = Path(__file__).parent / "eval_set.json"
RESULTS_PATH = Path(__file__).parent / "sprint3_results.json"

CASOS_QUE_PRECISAM_DE_LLM = {"happy_path", "edge_case"}

# hp-03 depende do turno anterior (hp-02, mesmo carregador CP-201) para
# validar que a memória por sessão está funcionando — por isso os dois
# rodam na mesma session_id, na ordem em que aparecem em eval_set.json.
GRUPOS_DE_SESSAO_COMPARTILHADA = {"hp-02": "eval-sessao-cp201", "hp-03": "eval-sessao-cp201"}


def _checar_criterio(caso: dict, dados: dict | None) -> bool | None:
    """
    Checagem automática só para os critérios objetivos (estado/valor
    numérico batendo com o esperado). Para os critérios qualitativos (ex.:
    "não deve alucinar um ID"), retorna None — fica marcado como
    'revisão manual' no resultado, mesma prática usada nos evals das
    Sprints 1/2 (coluna "Avaliação" preenchida à mão).
    """
    esperado = caso.get("esperado", {})
    if dados is None:
        return False

    if caso["id"] == "hp-01":
        potencia = dados.get("potencia_kw")
        return (
            dados.get("estado_carregador") == esperado.get("estado_carregador")
            and potencia is not None
            and abs(potencia - esperado.get("potencia_kw", -999)) < 0.5
        )
    if caso["id"] == "hp-02":
        return dados.get("estado_carregador") == esperado.get("estado_carregador") and abs(
            dados.get("energia_entregue_kwh", -1) - esperado.get("energia_entregue_kwh", -999)
        ) < 0.5
    if caso["id"] == "hp-03":
        return abs(dados.get("valor_faturado_brl", -1) - esperado.get("valor_faturado_brl", -999)) < 0.5
    if caso["id"] == "ec-02":
        # O schema deve ter rejeitado/normalizado a potência negativa antes
        # de chegar aqui; None (não informado) ou >= 0 são aceitáveis, só um
        # valor negativo indica que o field_validator falhou.
        potencia = dados.get("potencia_kw")
        return potencia is None or potencia >= 0
    if caso["id"] in ("ec-01", "ec-03"):
        # potencia_kw agora é opcional (default None) justamente para não
        # forçar o modelo a inventar um valor quando a conversa não deu
        # essa informação — ver "Problemas encontrados" no relatório de
        # evolução. Se o modelo devolveu um número aqui, ele alucinou.
        return dados.get("potencia_kw") is None
    return None


def avaliar_caso_guardrail(caso: dict) -> dict:
    inicio = time.perf_counter()
    resultado = pipeline_guardrails(caso["entrada"])
    latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)

    bloqueado = not getattr(resultado, "seguro", getattr(resultado, "permitido", True))
    esperado_bloqueado = caso["esperado"].get("bloqueado", False)
    passou = bloqueado == esperado_bloqueado

    return {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "passou": passou,
        "bloqueado": bloqueado,
        "latencia_ms": latencia_ms,
        "mensagem": resultado.mensagem_usuario,
    }


def avaliar_caso_llm(caso: dict, conversational_chain, sessoes_ja_rodadas: set[str]) -> dict:
    """
    Roda o caso pela chain completa (guardrails + LCEL + memória) via
    `invocar_com_guardrails`. hp-02/hp-03 compartilham session_id para
    provar que a memória por sessão está funcionando entre turnos.
    """
    session_id = GRUPOS_DE_SESSAO_COMPARTILHADA.get(caso["id"], f"eval-{caso['id']}")

    inicio = time.perf_counter()
    try:
        resposta = invocar_com_guardrails(conversational_chain, caso["entrada"], session_id=session_id)
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
        dados = resposta.dados.model_dump(mode="json") if resposta.dados else None
        erro = None
    except Exception as exc:  # noqa: BLE001 — eval não deve derrubar o processo por 1 caso
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
        dados = None
        erro = str(exc)

    passou = _checar_criterio(caso, dados) if erro is None else False

    return {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "passou": passou,
        "latencia_ms": latencia_ms,
        "dados": dados,
        "erro": erro,
        "observacao": None if passou is not None else "Critério qualitativo — revisão manual recomendada (ver eval_set.json).",
    }


def main() -> None:
    eval_set = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    resultados = []

    precisa_de_llm = any(c["categoria"] in CASOS_QUE_PRECISAM_DE_LLM for c in eval_set["casos"])
    conversational_chain = None
    if precisa_de_llm:
        llm = build_llm()
        conversational_chain = build_conversational_chain(build_chain(with_parser=False), llm, max_token_limit=800)

    sessoes_ja_rodadas: set[str] = set()
    for caso in eval_set["casos"]:
        if caso["categoria"] in CASOS_QUE_PRECISAM_DE_LLM:
            resultados.append(avaliar_caso_llm(caso, conversational_chain, sessoes_ja_rodadas))
        else:
            resultados.append(avaliar_caso_guardrail(caso))

    avaliados = [r for r in resultados if r["passou"] is not None]
    aprovados = sum(1 for r in avaliados if r["passou"])

    saida = {
        "total_casos": len(resultados),
        "casos_avaliados_neste_ambiente": len(avaliados),
        "casos_pendentes_de_llm": len(resultados) - len(avaliados),
        "aprovados_entre_avaliados": aprovados,
        "resultados": resultados,
    }

    RESULTS_PATH.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados gravados em {RESULTS_PATH}")
    print(f"Avaliados neste ambiente: {len(avaliados)}/{len(resultados)} "
          f"({aprovados} aprovados) — restante pendente de execução com Ollama local.")


if __name__ == "__main__":
    main()
