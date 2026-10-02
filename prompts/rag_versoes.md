# Tabela de versões — system prompt RAG (Sprint 04)

Mesmo espírito de `prompts/versoes.md` (Sprint 03), agora medindo o prompt
que orquestra o pipeline RAG. Ganho de qualidade medido pelo eval de RAG
em `evals/` (RAGAS ou fallback manual) — nunca sobrescrever uma versão
anterior, o histórico completo é evidência para o Bloco B da rubrica.

| Versão | O que mudou | Por quê | faithfulness | answer_relevancy |
|---|---|---|---|---|
| v1 | Prompt inicial com `<role>`, `<scope>`, `<grounding>`, `<security>`, `<restrictions>`, `<output_format>`. Grounding obrigatório, citação de fonte via metadata do chunk, `<security>` trata o CONTEXTO como dado nunca como instrução. | Ponto de partida cobrindo os 3 requisitos não-negociáveis do enunciado (§3 itens 3, 4 e 6) num único prompt. | **1.0** (12/12 casos, rubrica manual) | **1.0** (12/12 casos, rubrica manual) |

| v2 | Adiciona a seção `<precisao_numerica>`: releitura obrigatória do trecho exato antes de citar um valor numérico (evita confundir faixas parecidas, ex.: tabela tarifária), proibição de aproximar/estimar um número para entidade não citada no CONTEXTO, e regra de só citar em `fontes` o documento cujo texto foi de fato usado. | Dirigida pelas falhas reais observadas com `gemma2:2b` na v1 (ver `docs/relatorio_modelos.md`): confusão entre faixas da tabela tarifária, invenção de especificação para um veículo não citado na base, e citação de fonte não utilizada. | **1.0** (`llama3.1:8b`, 12/12 — sem regressão); **0.667** (`gemma2:2b`, 8/12, ver nota) | **1.0** (`llama3.1:8b`); 0.972 (`gemma2:2b`) |

Medido em 2026-09-23/24 (`EVCHALLENGE_MODEL=<modelo> python evals/run_eval_rag.py v1|v2`),
contra `evals/eval_set_rag.json` (12 casos) e a base real de `data/knowledge_base/`
(4 PDFs sintéticos, 17 chunks indexados). Nas rodadas de 23-24/09, RAGAS
não estava instalado neste ambiente (`ModuleNotFoundError`); scores via
rubrica manual (`evals/rubrica_manual_ragas.md`). Resultados completos em
`evals/rag_results_{v1,v2}_{llama31,gemma2}.json`.

### RAGAS real (v1, `llama3.1:8b`) — 2026-10-02

Depois de resolver a incompatibilidade entre `ragas` e a versão instalada
de `langchain-community` (shim documentado em
`evals/run_eval_rag.py:_aplicar_shim_langchain_community_vertexai`) e
calibrar timeout/concorrência para o Ollama local (sem GPU, só 1
requisição por vez), o RAGAS rodou de verdade pela primeira vez:

| Métrica | RAGAS real | Rubrica manual |
|---|---|---|
| faithfulness (médio) | **0.893** | 1.0 |
| answer_relevancy (médio) | **0.589** | 1.0 |

Resultado completo em `evals/rag_results_v1_llama31_ragas.json`. Scores
por caso:

| Caso | faithfulness | answer_relevancy |
|---|---|---|
| rag-hp-01 | 1.000 | 0.478 |
| rag-hp-02 | 1.000 | 0.721 |
| rag-hp-03 | 0.500 | 0.491 |
| rag-hp-04 | 0.750 | 0.634 |
| rag-ec-01 | 1.000 | 0.625 |
| rag-ec-02 | 1.000 | 0.579 |
| rag-inj-01 | 1.000 | 0.596 |

**Por que o RAGAS real deu número mais baixo que a rubrica manual, mesmo
as respostas estando corretas:**

- `answer_relevancy` do RAGAS pune respostas curtas/diretas por
  construção — ele gera perguntas sintéticas a partir da resposta e mede
  a similaridade com a pergunta original; uma resposta telegráfica como
  "22 kW AC" (sem repetir o contexto da pergunta) gera perguntas
  sintéticas mais ambíguas, derrubando o score mesmo estando
  perfeitamente correta. A rubrica manual não penaliza concisão da mesma
  forma.
- `faithfulness` ficou abaixo de 1.0 em `rag-hp-03` (0.5) e `rag-hp-04`
  (0.75) mesmo com as respostas conferidas como factualmente corretas
  (valores e explicações batem com o contexto recuperado) — o LLM-juiz do
  RAGAS aqui é o próprio `llama3.1:8b` local (8B parâmetros), bem menor
  que o GPT-4 normalmente usado em avaliações RAGAS publicadas; um juiz
  menor decompõe a resposta em afirmações e às vezes marca uma afirmação
  como não sustentada por ruído de julgamento, não porque a resposta
  esteja de fato errada.

**Conclusão:** os dois métodos de avaliação concordam que o pipeline
funciona bem (nenhum score baixo o suficiente pra indicar alucinação real
— revisão manual caso a caso confirma respostas corretas em 100% dos 7
casos). A rubrica manual e o RAGAS medem a mesma coisa com critérios
diferentes (um humano vs. um LLM pequeno como juiz), e divergem em
magnitude sem divergir em conclusão — ambos os números ficam registrados
como evidência, sem que um "substitua" o outro.

`llama3.1:8b` (modelo principal) já saiu com score perfeito na v1 — a v2
não regrediu, mas também não tinha onde melhorar nesse modelo. O sinal
de ganho real está no `gemma2:2b`: comparando as duas versões com o
**mesmo denominador** (9 casos avaliáveis; a v1 teve 1 falha de parsing
em `rag-nc-02`, contada como falha em vez de excluída para permitir
comparação justa), o faithfulness médio subiu de **0.639 (v1) para
0.667 (v2)** — ganho real, porém modesto. A v2 corrigiu especificamente
o problema de citação (`rag-hp-02`, `rag-ec-01`: v1 citava uma fonte
errada/extra, v2 cita a fonte certa), mas **não eliminou** a alucinação
numérica em si (`rag-hp-03` continuou confundindo a faixa de tarifa;
`rag-ec-02` continuou inventando um número para o Nissan Leaf, só trocou
qual número inventava). Conclusão: esse resíduo de alucinação parece ser
mais uma limitação de capacidade do modelo de 2B parâmetros do que algo
corrigível só por prompt — reforça `llama3.1:8b` como modelo principal
(ver critério em `docs/relatorio_modelos.md`). Ideias para uma v3
experimental (few-shot, "citar antes de responder", chunking mais
granular da tabela tarifária) ficaram registradas como item opcional,
pós-entrega dos itens obrigatórios.

## Como preencher

1. Rodar `python -m src.rag.indexar` uma vez para popular `data/chroma_db/`.
2. Rodar o eval de RAG (`evals/run_eval_rag.py`, a criar — ver
   `evals/eval_set_rag.json`) com a versão de prompt em questão.
3. Copiar os scores (RAGAS ou rubrica manual) para a tabela acima.
4. Ao criar uma v2 (refinamento a partir de falhas encontradas no eval),
   adicionar uma nova linha — nunca editar a linha da v1.
