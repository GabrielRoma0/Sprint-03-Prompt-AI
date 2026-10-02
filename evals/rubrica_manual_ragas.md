# Rubrica manual — fallback do RAGAS

Usada por `evals/run_eval_rag.py` quando o pacote `ragas` não puder ser
executado neste ambiente (sem internet para o modelo-juiz, dependências
pesadas incompatíveis, etc. — ver `docs/relatorio_rag.md` para a
justificativa registrada nesta entrega). Equivalente a
`faithfulness` e `answer_relevancy` do RAGAS, aplicada manualmente (ou por
um script auxiliar) sobre o mesmo eval set (`evals/eval_set_rag.json`), a
cada iteração de prompt.

## faithfulness_manual (0–1)

Mede se a resposta só afirma coisas presentes no contexto recuperado.

| Score | Critério |
|---|---|
| 1.0 | Toda afirmação da resposta está literalmente sustentada por algum trecho do contexto recuperado. Citação de fonte presente e correta. |
| 0.75 | Afirmações sustentadas pelo contexto, mas a citação de fonte está incompleta/imprecisa (ex.: cita o documento errado entre os recuperados). |
| 0.5 | A resposta mistura conteúdo do contexto com pelo menos uma inferência razoável não explícita no texto (ex.: generaliza uma regra). |
| 0.25 | A resposta contém pelo menos uma afirmação que contradiz ou não tem base no contexto recuperado, mas o núcleo da resposta ainda é majoritariamente correto. |
| 0.0 | A resposta inventa informação (número, regra, especificação) que não está em nenhum trecho do contexto — alucinação. |

## answer_relevancy_manual (0–1)

Mede se a resposta de fato aborda a pergunta feita (não avalia se é
verdadeira — isso é `faithfulness_manual`).

| Score | Critério |
|---|---|
| 1.0 | Responde exatamente o que foi perguntado, sem informação irrelevante. |
| 0.75 | Responde a pergunta, mas inclui informação extra não pedida que dilui o foco. |
| 0.5 | Responde parcialmente — cobre parte da pergunta e ignora outra parte relevante. |
| 0.25 | Resposta tangencial — fala sobre o mesmo assunto geral mas não responde a pergunta específica. |
| 0.0 | Não responde a pergunta (incluindo recusas incorretas — ver regra abaixo). |

### Regra especial para casos `no_context`

Quando `esperado.respondeu_com_contexto = false` no eval set, a recusa
correta e explícita (explicando que a base não cobre o assunto) conta como
`answer_relevancy_manual = 1.0` e `faithfulness_manual = 1.0` — recusar
corretamente é o comportamento fiel esperado, não uma falha. Responder
com uma informação inventada nesses casos é sempre `faithfulness_manual = 0.0`.

## Como aplicar

1. Rodar `python evals/run_eval_rag.py` — se o RAGAS não estiver
   disponível/funcional, o script grava `evals/rag_results_v{N}.json` com
   os campos `faithfulness_manual` e `answer_relevancy_manual` como `null`
   e a resposta/contexto de cada caso prontos para revisão.
2. Um integrante do grupo aplica esta rubrica manualmente, caso a caso,
   preenchendo os dois campos no JSON gerado (0.0 a 1.0).
3. Calcular a média simples de cada métrica sobre os casos avaliáveis
   (excluindo `jailbreak`/`fora_de_escopo_dominio`, que são checados pelo
   guardrail, não pela rubrica) e registrar em `prompts/rag_versoes.md`.
4. Justificar no relatório de evolução (`docs/relatorio_evolucao.pdf`) por
   que o fallback manual foi necessário e por que estes dois critérios são
   equivalentes às métricas RAGAS que substituem (mesma definição de
   faithfulness/answer_relevancy do paper original do RAGAS, só que
   julgada por um humano em vez de um LLM-juiz).
