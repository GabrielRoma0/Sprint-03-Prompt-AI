# Relatório de uso de modelos e parâmetros

> Comparação exigida pela rubrica (Bloco B · §6 do enunciado): 2+ modelos,
> com `temperature`, `top_p` e `max_tokens` documentados.

## Nota sobre os modelos efetivamente testados

O enunciado (§3, item 1) pede `gpt-oss:120b` como modelo principal. Na
máquina usada para rodar e validar esta entrega (15 GB de RAM, sem GPU
dedicada), `gpt-oss:120b` não é viável de rodar localmente de forma
alguma — não é uma questão de tempo de download, mas de hardware: o
modelo (mesmo quantizado) exige da ordem de 60-70 GB de RAM/VRAM para
carregar, quase 5x a RAM total desta máquina. `qwen3:8b` também não estava
baixado localmente.

Avaliamos deliberadamente a opção de usar o **Ollama Cloud**, que oferece
`gpt-oss:120b-cloud` (inferência remota nos servidores da Ollama, sem
precisar do hardware local) — chegamos a registrar essa referência e
confirmar que existe. **Decidimos não usar**, por dois motivos: (1) isso
deixaria de ser inferência 100% local, o que era justamente um ponto
forte elogiado na avaliação da Sprint 2 ("Modelo local... sem API key,
privacidade total"); e (2) rodar via nuvem depende de cota/plano da conta
Ollama vinculada, o que se aproxima conceitualmente de depender de uma
API paga de terceiro — algo que o grupo optou por evitar por princípio,
não só por causa da regra do enunciado sobre não commitar API keys.

Para não entregar a comparação com números fictícios, ela foi rodada com
dois modelos já instalados localmente: **`llama3.1:8b`** (principal,
mesma ordem de grandeza de parâmetros que `qwen3:8b`) e **`gemma2:2b`**
(secundário — o mesmo modelo já usado como principal na Sprint 2, o que
também permite comparar diretamente com o baseline anterior). O código
(`src/chain/builder.py`, `src/chain/multi_provider.py`) aceita qualquer
modelo Ollama via parâmetro ou variável de ambiente
`EVCHALLENGE_MODEL`/`EVCHALLENGE_MODEL_SECUNDARIO` — em uma máquina com
hardware suficiente, basta rodar `ollama pull gpt-oss:120b` e
`ollama pull qwen3:8b` e repetir o comando abaixo para reproduzir a
comparação com os modelos exatos do enunciado.

## Modelos comparados

| Modelo | Papel no projeto | Onde é servido |
|---|---|---|
| `llama3.1:8b` | Modelo principal testado nesta entrega (substituindo `gpt-oss:120b`, indisponível localmente — ver nota acima) | Ollama local |
| `gemma2:2b` | Modelo secundário de comparação (menor, mais rápido; também o modelo principal usado na Sprint 2) | Ollama local |

## Parâmetros usados em cada teste

| Modelo | temperature | top_p | max_tokens | Observação |
|---|---|---|---|---|
| `llama3.1:8b` | 0.2 | 0.9 | 512 | Valor padrão de `build_llm()` (Etapa 1). Baixa temperature para reduzir variação no structured output. |
| `gemma2:2b` | 0.2 | 0.9 | 512 | Mesmos parâmetros do modelo principal, para isolar a variável "modelo" na comparação. |

## Como reproduzir a comparação (com os modelos do enunciado)

```bash
ollama pull gpt-oss:120b
ollama pull qwen3:8b
```

```bash
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b \
  python docs/comparar_modelos.py
```

## Resultados (medidos nesta entrega — `llama3.1:8b` vs. `gemma2:2b`)

Gerados por `docs/comparar_modelos.py` em 2026-09-20, rodando os 6 casos
`happy_path`/`edge_case` de `evals/eval_set.json` contra cada modelo
(resultado bruto em `docs/comparacao_modelos_resultado.json`).

| Modelo | Taxa de acerto no eval (happy path + edge case) | Latência média (ms) |
|---|---|---|
| `llama3.1:8b` | 5/6 (83,3%) | 20.207,80 |
| `gemma2:2b` | 4/6 (66,7%) | 21.920,79 |

`llama3.1:8b` teve tanto taxa de acerto maior quanto latência menor nesta
comparação, então foi mantido como o modelo usado para gerar o restante da
evidência desta entrega (`evals/sprint3_results.json`, `demo_etapa1.py`).

### Limitação encontrada: `format="json"` garante sintaxe, não o schema completo

`build_llm()` ativa o modo JSON nativo do Ollama (`format="json"`) para
evitar que o modelo responda em prosa livre (ver "Problemas encontrados" em
`docs/relatorio_evolucao.pdf`). Isso garante JSON sintaticamente válido, mas
não garante que todos os campos obrigatórios do schema estejam presentes: no
caso `hp-03` com `llama3.1:8b`, o modelo respondeu apenas
`{"valor_faturado_brl": 0.0}` (JSON válido, mas faltando o campo obrigatório
`estado_carregador`), e o `PydanticOutputParser` corretamente rejeitou essa
saída. Mitigação futura recomendada: usar decodificação restrita por JSON
Schema (não só "json" genérico) quando o provedor suportar, ou envolver o
parser com um `OutputFixingParser`/retry que reenvia o erro de validação ao
modelo para correção.

## Critério de escolha do modelo principal

`gpt-oss:120b` é o modelo indicado pelo enunciado (§3, item 1) e é o valor
padrão em `build_llm()`/`build_chain()` — o código está pronto para ele.
Nesta entrega ele foi substituído por `llama3.1:8b` apenas para conseguir
gerar evidência real de execução dentro do prazo (ver nota no topo deste
documento). Os números acima mostraram `gemma2:2b` com qualidade e latência
piores que `llama3.1:8b` nesta bateria de testes — o oposto do que se
esperaria só pelo tamanho do modelo, o que reforça que o comportamento de
seguir instruções de formato (JSON estrito) pesa tanto quanto o tamanho do
modelo para esta tarefa.

---

# Sprint 04 — modelos e parâmetros do pipeline RAG

> Continuação deste relatório para o pipeline RAG (`src/rag/`). A
> comparação acima (Sprint 03) é sobre a chain conversacional
> (`ConsultaRecarga`, dados de sessão simulados); esta seção compara os
> mesmos modelos candidatos, mas gerando respostas fundamentadas na base
> de conhecimento vetorizada (`RespostaRAG`, com citação de fonte).
> Detalhamento técnico do pipeline em si (chunking, retriever, segurança)
> está em `docs/relatorio_rag.md` — aqui o foco é só modelo × parâmetros.

**Status: executado.** Base indexada (17 chunks) e eval rodado com os dois
modelos em 2026-09-23 (`evals/rag_results_v1_llama31.json`,
`evals/rag_results_v1_gemma2.json`) — resultados na tabela da seção
"Resultados" abaixo. RAGAS não estava instalado neste ambiente; scores
via rubrica manual (`evals/rubrica_manual_ragas.md`).

## Modelo de embedding (fixo, não comparado)

| Modelo | Papel | Onde é servido |
|---|---|---|
| `nomic-embed-text` | Gera os vetores da base de conhecimento e das perguntas (indexação e busca) | Ollama local (`src/rag/embeddings.py`) |

Pedido explicitamente pelo enunciado (§1) — não é um dos "2+ modelos"
comparados abaixo; a comparação de modelos da rubrica (Bloco C) é sobre o
**modelo de resposta** (o LLM que lê o contexto recuperado e gera a
resposta citando fonte), não sobre o modelo de embedding.

## Modelos de resposta comparados

Mesmo par já validado no pipeline conversacional da Sprint 03 (seção
acima), agora testado sobre o pipeline RAG — reaproveitar o par já
instalado localmente evita reintroduzir a limitação de hardware descrita
na nota do topo deste documento.

| Modelo | Papel no pipeline RAG | Onde é servido |
|---|---|---|
| `llama3.1:8b` | Modelo principal — mesmo escolhido na Sprint 03 por ter tido melhor taxa de acerto e menor latência no eval conversacional | Ollama local |
| `gemma2:2b` | Modelo secundário de comparação | Ollama local |

Reproduzir com os modelos do enunciado (`gpt-oss:120b`/`qwen3:8b`) em uma
máquina com hardware suficiente: mesma variável de ambiente
`EVCHALLENGE_MODEL`, já lida por `build_llm()` (reaproveitado em
`src/rag/rag_chain.py`).

## Parâmetros usados no pipeline RAG

| Parâmetro | Valor | Por quê difere (ou não) da Sprint 03 |
|---|---|---|
| `temperature` | **0.0** | Reduzido de 0.2 (Sprint 03) — RAG prioriza reprodutibilidade e aderência literal ao contexto recuperado sobre variação; queremos o mesmo contexto sempre gerando a mesma citação. |
| `top_p` | 0.9 | Mantido igual à Sprint 03, para isolar `temperature` como a única variável de amostragem alterada entre as duas chains. |
| `top_k` (retriever, não confundir com top-k de amostragem do LLM) | 4 | Quantos chunks o retriever traz por pergunta (`src/rag/retriever.py`). Não existe na chain conversacional da Sprint 03 — é específico do RAG. Mais chunks = mais chance de cobrir a resposta certa, às custas de mais tokens por chamada. |
| `max_tokens` | Não fixado explicitamente (usa o default do modelo via `ChatOllama`) | A resposta RAG (`RespostaRAG`) é mais curta que `ConsultaRecarga` em média — texto livre + lista de fontes, sem necessidade de um teto customizado até agora. Se algum caso do eval mostrar resposta cortada, fixar aqui e justificar o valor escolhido. |

## Como rodar a comparação

```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b
ollama pull gemma2:2b

python -m src.rag.indexar   # indexa data/knowledge_base/ uma vez

EVCHALLENGE_MODEL=llama3.1:8b python evals/run_eval_rag.py v1
EVCHALLENGE_MODEL=gemma2:2b python evals/run_eval_rag.py v1
```

Cada execução grava `evals/rag_results_v1.json` — rodar para um modelo,
copiar/renomear o arquivo (ex.: `rag_results_v1_llama31.json`) antes de
rodar para o outro, para não sobrescrever.

## Resultados (medidos em 2026-09-23, `evals/eval_set_rag.json`, rubrica manual)

| Modelo | faithfulness (manual) | answer_relevancy (manual) | Latência média (ms, casos RAG) | Casos `no_context` recusados corretamente |
|---|---|---|---|---|
| `llama3.1:8b` | **1.0** (12/12 casos automáticos aprovados) | **1.0** | 94.869 | 2/2 |
| `gemma2:2b` | **0.594** (8/12 casos automáticos aprovados) | 0.969 | 50.263 | 0/2 |

Detalhe caso a caso em `evals/rag_results_v1_llama31.json` e
`evals/rag_results_v1_gemma2.json`. Falhas concretas do `gemma2:2b`
(explicam o faithfulness baixo):

- **Alucinação de valor**: confundiu as 3 faixas da tabela tarifária,
  respondendo R$ 0,85/kWh (intermediário) para uma pergunta sobre o
  horário de ponta (correto: R$ 1,20/kWh) — `llama3.1:8b` acertou o mesmo
  caso.
- **Alucinação em edge case**: inventou que o Nissan Leaf "atinge carga em
  torno de 22 kW", um dado que não existe em nenhum documento da base —
  exatamente o comportamento que o caso `rag-ec-02` foi desenhado para
  detectar. `llama3.1:8b` recusou corretamente dar um número específico
  no mesmo caso.
- **Citação fabricada em recusa**: no caso `rag-nc-01` (fora da base), o
  texto da resposta recusou corretamente, mas o campo estruturado saiu
  `respondeu_com_contexto=True` citando uma fonte que não sustenta nada
  do que foi dito — inconsistência entre o texto livre e o schema.
- **Falha de parsing**: no caso `rag-nc-02`, o modelo devolveu
  `respondeu_com_contexto`/`fontes` como string (`"false"`/`"[]"`) em vez
  do tipo esperado pelo schema, e o `PydanticOutputParser` rejeitou a
  saída — mesma classe de limitação de modelo pequeno com `format="json"`
  já documentada na comparação da Sprint 03 (seção acima).

`gemma2:2b` foi ~1,9x mais rápido, mas a diferença de latência não
compensa a taxa de alucinação/inconsistência observada num pipeline cujo
requisito central (§3, item 3 do enunciado) é justamente não inventar
informação fora do contexto.

## Critério de escolha do modelo principal (RAG)

`llama3.1:8b` é o modelo principal também para o RAG, pelo mesmo motivo
da Sprint 03 (seção acima) reforçado pelos números desta tabela:
zero alucinações e 100% de recusa correta em `no_context` contra 2
alucinações concretas e 0/2 de recusa correta em `gemma2:2b` — para um
pipeline cujo requisito não-negociável é grounding, fidelidade ao
contexto pesa mais que a latência ~2x menor do modelo menor.
