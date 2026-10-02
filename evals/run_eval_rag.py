"""
Reexecuta evals/eval_set_rag.json sobre o pipeline RAG (src/rag/) e grava
evals/rag_results_{prompt_version}.json.

- Casos "jailbreak" e "fora_de_escopo_dominio" rodam só contra os
  guardrails (src/guardrails), sem precisar do retriever/LLM — mesmo
  comportamento da Sprint 03 (evals/run_eval.py).
- Casos "happy_path", "edge_case", "no_context" e
  "prompt_injection_documento" precisam do vector store já indexado
  (rode `python -m src.rag.indexar` antes) e do Ollama local rodando.

Avaliação de faithfulness/answer_relevancy:
- Tenta usar RAGAS (LLM-juiz = o próprio ChatOllama local, sem API paga).
- Se RAGAS não estiver instalado ou a chamada falhar por qualquer motivo
  (API do pacote muda entre versões, dependência pesada ausente, etc.),
  cai automaticamente no fallback documentado em
  evals/rubrica_manual_ragas.md: grava os campos como `null`, prontos
  para preenchimento manual por um integrante do grupo.

Uso:
    python evals/run_eval_rag.py [versao_do_prompt]
    # ex.: python evals/run_eval_rag.py v1
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.guardrails.moderation import pipeline_guardrails  # noqa: E402
from src.rag.prompt_rag import PROMPT_RAG_VERSAO_PADRAO  # noqa: E402
from src.rag.rag_chain import build_rag_chain  # noqa: E402
from src.rag.retriever import build_retriever  # noqa: E402
from src.rag.vector_store import carregar_vector_store  # noqa: E402

EVAL_SET_PATH = Path(__file__).parent / "eval_set_rag.json"

CATEGORIAS_SO_GUARDRAIL = {"jailbreak", "fora_de_escopo_dominio"}
CATEGORIAS_RAG = {"happy_path", "edge_case", "no_context", "prompt_injection_documento"}


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


def _checar_criterio_rag(caso: dict, resposta, contextos: list[str]) -> bool | None:
    """
    Checagem automática só para os critérios objetivos
    (respondeu_com_contexto / presença de fontes). Critérios qualitativos
    (ex.: "não afirma uma relação que não está no texto") ficam None —
    revisão manual, mesma prática de evals/run_eval.py.

    Dois critérios objetivos, combináveis no mesmo caso:
    - `respondeu_com_contexto` (+ opcionalmente `cita_fonte`): bate o
      booleano e, se esperado grounded, exige `fontes` não vazio.
    - `resposta_deve_conter`: lista de substrings (qualquer uma bastando,
      ex.: variações "1,20"/"1.20") que devem aparecer na resposta —
      checagem literal do valor citado (ex.: "22 kW", "R$ 1,20"), não uma
      avaliação de qualidade (isso é papel do RAGAS/rubrica manual).
    """
    esperado = caso.get("esperado", {})
    resultado: bool | None = None

    if "respondeu_com_contexto" in esperado:
        resultado = resposta.respondeu_com_contexto == esperado["respondeu_com_contexto"]
        if resultado and esperado["respondeu_com_contexto"] and esperado.get("cita_fonte") and not resposta.fontes:
            resultado = False

    trechos_esperados = esperado.get("resposta_deve_conter")
    if trechos_esperados:
        contem_trecho = any(t.lower() in resposta.resposta.lower() for t in trechos_esperados)
        resultado = contem_trecho if resultado is None else (resultado and contem_trecho)

    return resultado


def avaliar_caso_rag(caso: dict, retriever, chain) -> dict:
    inicio = time.perf_counter()
    try:
        documentos = retriever.invoke(caso["entrada"])
        contextos = [d.page_content for d in documentos]
        resposta = chain.invoke({"pergunta": caso["entrada"]})
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
        erro = None
    except Exception as exc:  # noqa: BLE001 — eval não deve derrubar o processo por 1 caso
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
        resposta = None
        contextos = []
        erro = str(exc)

    passou = _checar_criterio_rag(caso, resposta, contextos) if erro is None else False

    return {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "passou": passou,
        "latencia_ms": latencia_ms,
        "pergunta": caso["entrada"],
        "resposta": resposta.resposta if resposta else None,
        "respondeu_com_contexto": resposta.respondeu_com_contexto if resposta else None,
        "fontes": resposta.fontes if resposta else [],
        "contextos_recuperados": contextos,
        "erro": erro,
        "faithfulness": None,
        "answer_relevancy": None,
        "observacao": None if passou is not None else "Critério qualitativo — revisão manual (ver eval_set_rag.json).",
    }


def _aplicar_shim_langchain_community_vertexai() -> None:
    """
    Contorno de incompatibilidade entre `ragas` e a versão de
    `langchain-community` instalada neste projeto.

    `ragas.llms.base` importa `ChatVertexAI` de
    `langchain_community.chat_models.vertexai` só para incluir numa lista
    usada em `isinstance()` (`MULTIPLE_COMPLETION_SUPPORTED`) — nunca é
    usado de fato, já que o LLM deste projeto é sempre `ChatOllama`.
    Nesta versão de `langchain-community` (que está sendo sunset/
    descontinuada, ver aviso de deprecação do próprio pacote), esse
    submódulo específico não existe mais, e a importação quebra o `ragas`
    inteiro por causa disso — sem precisar de nenhuma integração com
    Google Vertex AI de verdade.

    Registrar um módulo/classe substituta em `sys.modules` antes do
    `import ragas` resolve sem precisar fazer downgrade de
    `langchain-community`/`langchain-core` (arriscado: quebraria
    `langchain-chroma`/`langchain-ollama`, já validados no resto do
    pipeline RAG). Idempotente — não faz nada se o import real já
    funcionar (versões futuras de ragas/langchain-community sem esse gap).
    """
    import sys
    import types

    try:
        import langchain_community.chat_models.vertexai  # noqa: F401

        return  # já funciona nativamente, nada a fazer
    except ModuleNotFoundError:
        pass

    shim = types.ModuleType("langchain_community.chat_models.vertexai")

    class ChatVertexAI:  # nunca instanciado de verdade neste projeto
        pass

    shim.ChatVertexAI = ChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = shim


def _tentar_ragas(resultados_rag: list[dict]) -> tuple[bool, str | None]:
    """
    Preenche `faithfulness`/`answer_relevancy` em `resultados_rag` in-place
    usando RAGAS, com o próprio ChatOllama local como LLM-juiz (sem API
    paga). Retorna (sucesso, motivo_da_falha).

    Só avalia casos que de fato geraram uma resposta (erro is None) e que
    responderam com contexto — RAGAS faithfulness/answer_relevancy não se
    aplicam a uma recusa `respondeu_com_contexto=False` sem contextos.
    """
    avaliaveis = [r for r in resultados_rag if r["erro"] is None and r["respondeu_com_contexto"]]
    if not avaliaveis:
        return True, "Nenhum caso respondido com contexto nesta execução — RAGAS não teve o que avaliar."

    try:
        _aplicar_shim_langchain_community_vertexai()

        from ragas import EvaluationDataset, evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import AnswerRelevancy, Faithfulness
        from ragas.run_config import RunConfig

        from src.chain.builder import build_llm
        from src.rag.embeddings import build_embeddings

        llm_juiz = LangchainLLMWrapper(build_llm(temperature=0.0))
        embeddings_juiz = LangchainEmbeddingsWrapper(build_embeddings())

        dataset = EvaluationDataset.from_list(
            [
                {
                    "user_input": r["pergunta"],
                    "response": r["resposta"],
                    "retrieved_contexts": r["contextos_recuperados"],
                }
                for r in avaliaveis
            ]
        )

        resultado = evaluate(
            dataset=dataset,
            metrics=[Faithfulness(), AnswerRelevancy()],
            llm=llm_juiz,
            embeddings=embeddings_juiz,
            # timeout alto + max_workers=1: o Ollama local roda com -np 1
            # (uma requisição por vez); o default do RAGAS (timeout=180s,
            # max_workers=16) manda 16 chamadas concorrentes contra um
            # servidor que só atende 1 por vez, e cada chamada sozinha já
            # pode levar >180s sem GPU — dava timeout em 100% dos casos
            # antes desse ajuste (calibrado empiricamente: ~270s por caso
            # com as duas métricas, rodando serializado).
            run_config=RunConfig(timeout=1800, max_workers=1, max_retries=2),
        )
        df = resultado.to_pandas()

        for i, r in enumerate(avaliaveis):
            r["faithfulness"] = float(df.iloc[i]["faithfulness"])
            r["answer_relevancy"] = float(df.iloc[i]["answer_relevancy"])

        return True, None
    except Exception as exc:  # noqa: BLE001 — qualquer falha do RAGAS cai no fallback manual
        return False, f"{type(exc).__name__}: {exc}"


def main() -> None:
    prompt_version = sys.argv[1] if len(sys.argv) > 1 else PROMPT_RAG_VERSAO_PADRAO
    eval_set = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))

    precisa_de_rag = any(c["categoria"] in CATEGORIAS_RAG for c in eval_set["casos"])
    retriever = chain = None
    if precisa_de_rag:
        vector_store = carregar_vector_store()
        retriever = build_retriever(vector_store)
        chain = build_rag_chain(retriever, prompt_version=prompt_version)

    resultados = []
    for caso in eval_set["casos"]:
        if caso["categoria"] in CATEGORIAS_SO_GUARDRAIL:
            resultados.append(avaliar_caso_guardrail(caso))
        else:
            resultados.append(avaliar_caso_rag(caso, retriever, chain))

    resultados_rag = [r for r in resultados if r["categoria"] in CATEGORIAS_RAG]
    ragas_ok, motivo_fallback = _tentar_ragas(resultados_rag)

    avaliados = [r for r in resultados if r["passou"] is not None]
    aprovados = sum(1 for r in avaliados if r["passou"])

    com_score = [r for r in resultados_rag if r.get("faithfulness") is not None]
    media_faithfulness = round(sum(r["faithfulness"] for r in com_score) / len(com_score), 3) if com_score else None
    media_answer_relevancy = (
        round(sum(r["answer_relevancy"] for r in com_score) / len(com_score), 3) if com_score else None
    )

    saida = {
        "prompt_version": prompt_version,
        "avaliacao_ragas_executada": ragas_ok and bool(com_score),
        "motivo_fallback_manual": None if (ragas_ok and com_score) else (
            motivo_fallback or "RAGAS não indisponibilizou scores — preencher manualmente (ver evals/rubrica_manual_ragas.md)."
        ),
        "total_casos": len(resultados),
        "casos_avaliados_automaticamente": len(avaliados),
        "aprovados_entre_avaliados": aprovados,
        "media_faithfulness": media_faithfulness,
        "media_answer_relevancy": media_answer_relevancy,
        "resultados": resultados,
    }

    results_path = Path(__file__).parent / f"rag_results_{prompt_version}.json"
    results_path.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Resultados gravados em {results_path}")
    print(f"Critério automático: {aprovados}/{len(avaliados)} aprovados "
          f"({len(resultados) - len(avaliados)} pendentes de revisão manual qualitativa).")
    if saida["avaliacao_ragas_executada"]:
        print(f"RAGAS — faithfulness médio: {media_faithfulness}, answer_relevancy médio: {media_answer_relevancy}")
    else:
        print(f"RAGAS indisponível ({saida['motivo_fallback_manual']}). "
              f"Preencher faithfulness/answer_relevancy manualmente em {results_path} "
              "seguindo evals/rubrica_manual_ragas.md.")


if __name__ == "__main__":
    main()
