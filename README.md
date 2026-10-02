# EV Challenge — GoodWe — Sprints 03 e 04

Disciplina Prompt and Artificial Intelligence — FIAP, Ciência da Computação,
turma 1CCR, semestre 2026.2. Parceiro: GoodWe Brasil.

Este repositório é a continuidade do projeto EV Challenge GoodWe entre as
Sprints 1/2 (semestre anterior), a Sprint 03 (refactory conversacional em
LangChain) e a Sprint 04 (RAG medido + interface web). Cada sprint tem sua
própria seção abaixo — o código é aditivo: nada da Sprint 03 foi removido
ou reescrito para a Sprint 04, só estendido.

> **Nota sobre o nome do repositório:** o link no GitHub continua
> `Sprint-03-Prompt-AI` porque o projeto é contínuo (criado originalmente
> na Sprint 03) — não é um repositório separado nem desatualizado. Todo o
> conteúdo da Sprint 04 está aqui dentro, na seção própria abaixo.

- **[Sprint 03 — Refactory conversacional em LangChain](#sprint-03--refactory-conversacional-em-langchain)**
- **[Sprint 04 — Pipeline RAG, avaliação e interface web](#sprint-04--pipeline-rag-avaliação-e-interface-web)**

---

## Sprint 03 — Refactory conversacional em LangChain

O objetivo desta etapa foi reconstruir o núcleo conversacional do chatbot
usando a stack do Módulo 1 da disciplina (LangChain LCEL, memória
conversacional, structured output com Pydantic v2 e context engineering),
mantendo a inferência 100% local via Ollama, sem uso de nenhuma API paga.

### Equipe

| Nome | RM | Função no projeto |
|---|---|---|
| Léo Moreno Sambo | 569556 | Chain LCEL (`prompt \| llm \| parser`) e memória conversacional por sessão |
| Fernando Hideki Rosa Oda | 571408 | Structured output — schema Pydantic v2 do domínio EV (`ConsultaRecarga`) |
| Gabriel Botelho Romão | 570589 | System prompt versionado e context engineering; coordenação técnica geral |
| Thor Ferreira Camargo | 569543 | Guardrails de segurança — jailbreak/prompt injection e validação de escopo |
| Rafael Marinucci Peres | 569729 | Eval set e reexecução dos testes |
| David dos Reis Cardoso | 568938 | Comparação de modelos e implementação do bônus multi-provider |

Todos colaboraram na consolidação final do relatório de evolução
(`docs/relatorio_evolucao.pdf`).

### Contexto do projeto

O chatbot EV Challenge GoodWe responde consultas sobre o estado de
carregadores de veículos elétricos: se estão disponíveis, em carga ou com
falha, qual a potência entregue, quanta energia já foi consumida numa
sessão e quanto já foi faturado. Nas Sprints 1 e 2, esse núcleo foi
implementado de forma manual: uma classe Python chamando o Ollama
diretamente, com o system prompt embutido como string fixa no código
(sem versionamento nem medição de tokens), memória de conversa como uma
lista simples limitada a um número fixo de turnos, dados operacionais
simulados e sem validação estruturada da resposta do modelo (saída em
texto livre). A avaliação oficial da Sprint 2 documentou 7 casos de teste
manuais, dos quais 1 falhou (o chatbot recomendou a compra de um veículo
em vez de recusar por estar fora de escopo).

Nesta Sprint 03, esse núcleo foi reconstruído em cima do LangChain, usando
os conceitos do Módulo 1 da disciplina.

### O que foi implementado

#### Chain LCEL e memória por sessão

O núcleo do chatbot é uma chain declarativa `prompt | llm | parser`,
montada em `src/chain/builder.py` sobre `ChatOllama`. A memória
conversacional (`src/chain/memoria.py`) envolve essa chain com
`RunnableWithMessageHistory`, mantendo o histórico de cada sessão de
conversa limitado por um número máximo de tokens: quando o histórico
ultrapassa esse limite, as mensagens mais antigas são descartadas
automaticamente. Como o parser transforma a resposta do modelo num objeto
Pydantic (que `RunnableWithMessageHistory` não consegue gravar como
mensagem de histórico), a chain usada para memória é montada sem o
parser, e o parsing acontece depois, em `src/chain/guarded_chain.py`.

A demonstração em `demo_etapa1.py` roda 4 turnos numa mesma sessão e
imprime as mensagens retidas no histórico ao final, provando que a
memória persiste entre turnos (o modelo acumula corretamente potência,
energia entregue, valor faturado e o estado final do carregador ao longo
da conversa).

#### Structured output com Pydantic v2

`src/schemas/consulta_recarga.py` define o schema `ConsultaRecarga`, que
toda resposta do chatbot precisa satisfazer: estado do carregador (enum),
potência instantânea, energia entregue, valor faturado e uma observação
opcional. Cada campo numérico tem um `field_validator` que rejeita
valores fora da faixa esperada (ex.: potência negativa, ou acima do
catálogo GoodWe). O campo de potência é o único opcional do schema: ele
começou como obrigatório, mas o eval mostrou que isso forçava o modelo a
inventar um número quando a conversa não informava a potência — tornado
opcional, o modelo passou a responder `null` nesse caso, como esperado.

#### Context engineering e prompt versionado

O system prompt está em `prompts/`, com três versões incrementais,
escritas com marcação XML (`<role>`, `<scope>`, `<security>`,
`<restrictions>`, `<output_format>`, entre outras):

- **v1** (310 tokens): versão mínima, só para validar a chain.
- **v2** (619 tokens): adiciona defesa explícita contra jailbreak/prompt
  injection e exemplos de recusa.
- **v3** (834 tokens): restringe a regra de "não inventar valor" ao campo
  de potência especificamente (o único opcional no schema) e esclarece
  que perguntas sobre o valor já faturado de uma sessão não são
  aconselhamento financeiro.

Cada versão foi medida com `tiktoken` (`prompts/medir_tokens.py`), e a
tabela completa com o que mudou, por quê e o custo em tokens de cada
versão está em `prompts/versoes.md`.

#### Guardrails de segurança e escopo

`src/guardrails/` implementa dois guardrails determinísticos (baseados em
regras, não em outro modelo de linguagem), que rodam antes da chain LCEL
ser chamada:

- `moderation.py` detecta tentativas de jailbreak e prompt injection
  (pedidos para ignorar instruções anteriores, trocar de persona, revelar
  o system prompt, ou injetar comandos via delimitadores falsos).
- `scope_validator.py` recusa pedidos de aconselhamento jurídico,
  financeiro ou de segurança elétrica, sempre orientando o usuário a
  procurar um profissional habilitado.

Rodar os dois guardrails antes do modelo evita gastar uma chamada ao LLM
em mensagens já sabidamente maliciosas ou fora de escopo. Testados em
`demo_etapa2_guardrails.py`: 6 de 6 casos corretos.

#### Eval reexecutado

`evals/eval_set.json` reúne 11 casos de teste cobrindo os mesmos tipos de
cenário usados nas Sprints 1 e 2: 3 casos de happy path, 3 de edge case,
2 de tentativa de jailbreak e 3 de pedido fora de escopo. O script
`evals/run_eval.py` reexecuta todos os casos contra a versão atual do
chatbot (guardrails, quando aplicável, mais a chain completa com memória),
com checagem automática de critério quando o critério é objetivo (ex.:
estado do carregador bate com o esperado) e sinalização de revisão manual
quando o critério é qualitativo. Resultado registrado em
`evals/sprint3_results.json`: 11 de 11 casos aprovados.

#### Comparação de modelos e bônus multi-provider

`docs/relatorio_modelos.md` documenta a comparação entre dois modelos com
os mesmos parâmetros (`temperature=0.2`, `top_p=0.9`), incluindo a
justificativa de por que os modelos indicados no enunciado
(`gpt-oss:120b` e `qwen3:8b`) foram substituídos nesta entrega — não por
falta de tempo, mas porque a máquina usada para validar o projeto (15 GB
de RAM, sem GPU dedicada) não tem capacidade física para carregar um
modelo que exige da ordem de 60-70 GB mesmo quantizado. Avaliamos rodar
`gpt-oss:120b` via Ollama Cloud (inferência remota) e decidimos não usar,
por dois motivos: deixaria de ser inferência 100% local (um ponto forte
elogiado na avaliação da Sprint 2) e dependeria de cota de uma conta
externa, o que se aproxima de depender de uma API paga de terceiro.

Como bônus (`src/chain/multi_provider.py`, demonstrado em
`demo_bonus_multiprovider.py`), o chatbot também suporta consultar mais
de um modelo e mais de uma versão de prompt para a mesma pergunta,
retornando as respostas lado a lado.

#### Relatório de evolução do projeto

`docs/relatorio_evolucao.pdf` (gerado por
`docs/gerar_relatorio_evolucao.py`) reúne o resumo da evolução desde as
Sprints 1/2, as decisões técnicas da refatoração, a tabela obrigatória de
comparativo antes/depois (qualidade das respostas, tokens por turno,
latência, acurácia do structured output, casos de jailbreak e
out-of-scope bloqueados), cinco problemas encontrados durante o
desenvolvimento com a decisão tomada para cada um, e a divisão de
trabalho da equipe.

### Estrutura do repositório

```
prompts/
  system_prompt_v1.md        system prompt inicial
  system_prompt_v2.md        adiciona guardrails de segurança ao prompt
  system_prompt_v3.md        corrige alucinação de campo opcional
  versoes.md                 tabela de versões com tokens medidos
  medir_tokens.py            mede tokens de cada versão com tiktoken
src/
  chain/
    builder.py                chain LCEL (prompt | llm | parser)
    memoria.py                 memória por sessão com limite de tokens
    guarded_chain.py            ponto de entrada único (guardrails + chain)
    multi_provider.py           bônus: consulta múltiplos modelos/prompts
  schemas/
    consulta_recarga.py         schema Pydantic v2 do domínio EV
  guardrails/
    moderation.py                detecção de jailbreak/prompt injection
    scope_validator.py           validação de escopo GoodWe
evals/
  eval_set.json                 11 casos de teste
  run_eval.py                    reexecuta o eval
  sprint3_results.json           resultado: 11/11 aprovados
docs/
  relatorio_modelos.md          comparação de modelos e parâmetros
  comparar_modelos.py            script usado para gerar a comparação
  comparacao_modelos_resultado.json
  gerar_relatorio_evolucao.py   gera o PDF abaixo
  relatorio_evolucao.pdf         relatório de evolução do projeto
demo_etapa1.py                   demonstração da chain + memória (4 turnos)
demo_etapa2_guardrails.py        demonstração dos guardrails (6 casos)
demo_bonus_multiprovider.py      demonstração do bônus multi-provider
equipe.txt                        nome, RM, turma e função de cada integrante
.env.example                      variáveis de ambiente esperadas
.gitignore
requirements.txt
CHECKLIST_ENTREGA.md              status detalhado de cada item da rubrica
```

### Como rodar

```bash
pip install -r requirements.txt

ollama serve

# Modelos usados nesta entrega (substitutos — ver docs/relatorio_modelos.md)
ollama pull llama3.1:8b
ollama pull gemma2:2b

cp .env.example .env   # preencher se necessário; nunca commitar .env
```

```bash
# Chain LCEL + memória por sessão
python demo_etapa1.py

# Guardrails (não depende do Ollama)
python demo_etapa2_guardrails.py

# Medição de tokens dos prompts
python prompts/medir_tokens.py

# Eval completo
python evals/run_eval.py

# Comparação de modelos
python docs/comparar_modelos.py

# Bônus: multi-provider
python demo_bonus_multiprovider.py

# Regenerar o relatório de evolução em PDF
python docs/gerar_relatorio_evolucao.py
```

Modelo e versão de prompt podem ser trocados por variável de ambiente sem
alterar código, por exemplo para reproduzir com os modelos indicados no
enunciado original em uma máquina com hardware suficiente:

```bash
ollama pull gpt-oss:120b
ollama pull qwen3:8b
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python evals/run_eval.py
```

### Resultados

- Eval reexecutado: 11 de 11 casos aprovados (`evals/sprint3_results.json`).
- Guardrails: 6 de 6 casos corretos (`demo_etapa2_guardrails.py`).
- Comparação de modelos: `llama3.1:8b` com 5/6 no eval e latência média de
  20,2 s; `gemma2:2b` com 4/6 e 21,9 s (`docs/comparacao_modelos_resultado.json`).
- Bônus multi-provider: 3 de 3 combinações de modelo/prompt testadas.

---

## Sprint 04 — Pipeline RAG, avaliação e interface web

**Status: em desenvolvimento.** Esta seção documenta o que já existe no
repositório; os itens marcados como pendentes ainda precisam ser
preenchidos até a entrega (23/10).

Continuidade direta da Sprint 03: o núcleo conversacional (chain LCEL,
guardrails, structured output) não foi alterado. A Sprint 04 adiciona uma
camada de RAG por cima dele — respostas passam a ser fundamentadas numa
base de conhecimento vetorizada (manuais GoodWe, regimentos de
carregamento compartilhado, FAQs, tabelas tarifárias), com citação de
fonte obrigatória, avaliação quantitativa (RAGAS) e uma interface web.

### Equipe — Sprint 04

| Nome | RM | Função no projeto |
|---|---|---|
| Léo Moreno Sambo | 569556 | Chain RAG end-to-end (`retriever \| prompt_rag \| llm \| parser`) — `src/rag/rag_chain.py`, `src/rag/retriever.py` |
| Fernando Hideki Rosa Oda | 571408 | Structured output do RAG — schema Pydantic v2 `RespostaRAG` com validação de citação obrigatória — `src/schemas/resposta_rag.py` |
| Gabriel Botelho Romão | 570589 | Prompt RAG versionado (v1/v2) e pipeline de indexação (loader, chunking, embeddings) — `prompts/rag_*.md`, `src/rag/`; coordenação técnica geral |
| Thor Ferreira Camargo | 569543 | Segurança do RAG — auditoria de prompt injection via documento e correção dos gaps de guardrail encontrados durante o eval — `src/guardrails/` |
| Rafael Marinucci Peres | 569729 | Eval set e execução do RAG (RAGAS/fallback manual) — `evals/eval_set_rag.json`, `evals/run_eval_rag.py`, `evals/rubrica_manual_ragas.md` |
| David dos Reis Cardoso | 568938 | Comparação de modelos sobre o pipeline RAG e interface web — `docs/relatorio_modelos.md` (seção Sprint 04), `app/` |

Todos colaboraram na consolidação final do relatório de evolução
(`docs/relatorio_evolucao_sprint04.pdf`). Divisão mantém a mesma frente
técnica de cada integrante já usada na Sprint 03, agora aplicada à versão
RAG do projeto — mesma divisão também está em `equipe_sprint04.txt`
(formato exigido pelo enunciado, §10) e na seção 5 de
`docs/relatorio_evolucao_sprint04.pdf`.

**Nota sobre o histórico de commits:** nem todos os integrantes tinham
familiaridade com Git/GitHub neste momento do curso, então o histórico de
commits desta sprint não tem uma entrada de cada pessoa na mesma
proporção. Isso não reflete o nível real de contribuição — todos
participaram igualmente do desenvolvimento, divisão de tarefas e revisão
do conteúdo desta entrega, conforme a tabela acima.

### O que foi implementado até agora

#### Pipeline RAG (`src/rag/`)

- `loader.py` — carrega os PDFs de `data/knowledge_base/` com
  `PyMuPDFLoader`, preservando `source` (nome do arquivo) e `page` em
  cada `Document`.
- `chunking.py` — `RecursiveCharacterTextSplitter` (800 caracteres, 120 de
  overlap — trade-off documentado no próprio arquivo).
- `embeddings.py` — `nomic-embed-text` via Ollama (`OllamaEmbeddings`),
  mesmo padrão de override por variável de ambiente usado em
  `src/chain/builder.py`.
- `vector_store.py` — ChromaDB persistente em `data/chroma_db/`
  (gitignored; regenerado por `indexar.py`).
- `retriever.py` — busca por similaridade, top-k configurável (padrão 4).
- `prompt_rag.py` + `prompts/rag_prompt_v1.md` — prompt versionado com
  grounding obrigatório, citação de fonte e defesa contra prompt
  injection embutida em documento (trata o CONTEXTO recuperado sempre
  como dado, nunca como instrução).
- `rag_chain.py` — monta a chain completa
  (`retriever -> formata contexto -> prompt_rag -> llm -> parser`),
  reaproveitando `build_llm` da Sprint 03.
- `indexar.py` — script único (`python -m src.rag.indexar`) que roda
  loader → chunking → auditoria de segurança → indexação.

#### Structured output do RAG

`src/schemas/resposta_rag.py` define `RespostaRAG`: campo `resposta`,
`respondeu_com_contexto` (bool) e `fontes` (lista, obrigatória sempre que
`respondeu_com_contexto=True` — validado por `field_validator`, não só
por instrução de prompt).

#### Segurança — prompt injection via documento

`src/guardrails/document_sanitizer.py` audita os chunks recuperados da
base de conhecimento em busca dos mesmos padrões de jailbreak já
detectados em `src/guardrails/moderation.py` (agora aplicados ao conteúdo
do documento, não à mensagem do usuário) — segunda camada de defesa além
da instrução `<security>` do próprio prompt RAG.

#### Interface web (`app/`)

`app/main.py` — Streamlit consumindo a chain RAG, passando cada pergunta
pelos guardrails existentes antes de responder, com a(s) fonte(s) exibidas
de forma visível abaixo da resposta (ou aviso explícito quando a base não
cobre a pergunta). Instruções de execução em `app/README.md`.

### Pendente

- [x] Popular `data/knowledge_base/` com PDFs do domínio (4 documentos:
      manual do produto, regimento condominial, FAQ, tabela tarifária).
      **Nota:** são documentos **sintéticos**, escritos pelo grupo (não
      são material oficial da GoodWe) — gerados por
      `data/knowledge_base/_gerar_pdfs_sinteticos.py` (reportlab), cada um
      com aviso dessa natureza na primeira página. Ver justificativa em
      `data/knowledge_base/README.md`.
- [x] Rodar `python -m src.rag.indexar` e validar a indexação — 5 páginas
      → 17 chunks, nenhum chunk suspeito, `data/chroma_db/` populado.
- [x] `evals/eval_set_rag.json` + `evals/run_eval_rag.py` — 12 casos
      ajustados ao conteúdo real dos 4 PDFs. **Rodado com `llama3.1:8b`:
      12/12 aprovados**, faithfulness e answer_relevancy médios = 1.0 via
      rubrica manual (RAGAS não instalado neste ambiente). Resultado em
      `evals/rag_results_v1_llama31.json`. Achado no processo: o eval
      expôs 2 gaps reais nos guardrails da Sprint 03 (regex não cobria
      "finja que você não tem restrição" nem o verbo "financiar") — **já
      corrigidos** em `src/guardrails/moderation.py` e `scope_validator.py`,
      sem regressão (`demo_etapa2_guardrails.py` continua 6/6).
- [x] **RAGAS real instalado e rodado** (2026-10-02, não só o fallback
      manual) — resolvido um conflito de dependência com
      `langchain-community` (shim em `run_eval_rag.py`) e calibrado
      timeout/concorrência pro Ollama local sem GPU. Resultado v1
      `llama3.1:8b`: **faithfulness médio 0.893, answer_relevancy médio
      0.589** (vs. 1.0/1.0 da rubrica manual — divergência de magnitude
      explicada e documentada, não de conclusão: revisão manual confirma
      respostas corretas nos 7 casos avaliáveis). Detalhe completo em
      `prompts/rag_versoes.md` e `docs/relatorio_rag.md` (seção 6),
      resultado bruto em `evals/rag_results_v1_llama31_ragas.json`.
- [x] **2ª iteração do prompt (v2) — completa, com ganho medido.**
      `prompts/rag_prompt_v2.md` adiciona `<precisao_numerica>`, dirigida
      pelas falhas reais do `gemma2:2b` (não pelo teste de injection, que
      já passou perfeito na v1 — ver abaixo). `llama3.1:8b` manteve 12/12
      (sem regressão); `gemma2:2b` foi de 0.639→0.667 de faithfulness
      (denominador consistente) — ganho real mas modesto: corrigiu
      citação de fonte, não eliminou a alucinação numérica em si.
      Resultados completos em `evals/rag_results_{v1,v2}_{llama31,gemma2}.json`,
      tabela consolidada em `prompts/rag_versoes.md` e
      `docs/relatorio_rag.md` (seção 6). Ideia de v3 experimental
      registrada como opcional, pós-entrega.
- [x] Teste de prompt injection real (`rag-inj-01`): PDF adversarial
      gerado à parte, as duas camadas de defesa (auditoria +
      `<security>` no prompt) resistiram — `llama3.1:8b`/v1 ignorou
      completamente a instrução embutida. Resultado em
      `docs/relatorio_rag.md`, seção 5.1.
- [x] `docs/relatorio_rag.md` — detalhamento técnico do pipeline (decisões
      de chunking, base montada, trade-offs, segurança e avaliação).
      **Pendente:** preencher as seções marcadas como "a preencher"
      (contagem de chunks, scores da tabela de avaliação) após indexar a
      base real e rodar o eval.
- [x] Atualizar `docs/relatorio_modelos.md` com a comparação de 2+ modelos
      rodando sobre o pipeline RAG. **Resultado real:** `llama3.1:8b`
      12/12 (faithfulness 1.0) vs. `gemma2:2b` 8/12 (faithfulness 0.594,
      2 alucinações concretas + 1 falha de parsing) — `llama3.1:8b`
      mantido como modelo principal. Detalhes na tabela "Resultados" do
      relatório.
- [x] Relatório de evolução do projeto em PDF (3 páginas, dentro do
      limite de 5) — `docs/gerar_relatorio_evolucao_sprint04.py` →
      `docs/relatorio_evolucao_sprint04.pdf`. Arquivo novo, separado do
      relatório já entregue da Sprint 03
      (`docs/gerar_relatorio_evolucao.py`/`relatorio_evolucao.pdf`, não
      alterados). Contém: resumo da evolução, decisões do pipeline RAG,
      tabela antes/depois obrigatória (Sprints 1/2 × Sprint 04), 3
      problemas encontrados com solução, e equipe/divisão de trabalho
      (mesma divisão de `equipe_sprint04.txt`, criado seguindo o formato
      do `equipe.txt` da Sprint 03). **Pendente:** essa divisão é uma
      proposta de continuidade da Sprint 03 — precisa ser
      confirmada/ajustada pela equipe de verdade antes da entrega (aviso
      já incluído nos dois arquivos).
- [x] Bônus (+1 pt): multi-provider no fluxo RAG. `src/rag/multi_provider.py`
      (mesmo padrão de `src/chain/multi_provider.py` da Sprint 03) roda 3
      combinações padrão (`llama3.1:8b`/v2, `llama3.1:8b`/v1,
      `gemma2:2b`/v2) contra o mesmo retriever. Demonstrado em
      `demo_bonus_multiprovider_rag.py` e integrado como toggle opcional
      ("Comparar múltiplos modelos/prompts") em `app/main.py`. **Testado
      de verdade (2026-09-25):** as 3 combinações responderam
      corretamente à pergunta de teste ("Qual a potência máxima...") com
      "22 kW AC" e fonte citada (`manual_chargegrid_evchargeops.pdf`).
      Latências: `llama3.1:8b`/v2 180,0s, `llama3.1:8b`/v1 134,7s,
      `gemma2:2b`/v2 51,6s (~3x mais rápido, mesma resposta correta neste
      caso).

### Estrutura adicionada nesta sprint

```
data/
  knowledge_base/            PDFs de origem (manuais, regimentos, FAQs, tarifas)
  chroma_db/                 vector store persistido (gitignored, gerado por indexar.py)
src/
  rag/
    loader.py                 carrega PDFs com PyMuPDFLoader
    chunking.py                RecursiveCharacterTextSplitter (800/120)
    embeddings.py               nomic-embed-text via Ollama
    vector_store.py              ChromaDB persistente
    retriever.py                  busca por similaridade (top-k)
    prompt_rag.py                  loader do prompt RAG versionado
    rag_chain.py                    chain RAG completa (retriever|prompt|llm|parser)
    indexar.py                       script de indexação (loader->chunking->auditoria->index)
    multi_provider.py                bônus: consulta múltiplos modelos/prompts no RAG
  guardrails/
    document_sanitizer.py       prompt injection via documento (base de conhecimento)
  schemas/
    resposta_rag.py              schema Pydantic v2 com fontes obrigatórias
prompts/
  rag_prompt_v1.md              system prompt RAG v1 (grounding + citação + security)
  rag_prompt_v2.md               v2 — reforço de precisão numérica
  rag_versoes.md                  tabela de versões do prompt RAG
evals/
  eval_set_rag.json             casos de teste do pipeline RAG
  run_eval_rag.py                 reexecuta o eval (RAGAS ou fallback manual)
  rubrica_manual_ragas.md          rubrica 0–1 equivalente ao RAGAS (fallback)
  rag_results_v1_llama31.json      resultado v1, llama3.1:8b (12/12)
  rag_results_v1_gemma2.json       resultado v1, gemma2:2b (8/12)
  rag_results_v2_llama31.json      resultado v2, llama3.1:8b (12/12, sem regressão)
  rag_results_v2_gemma2.json       resultado v2, gemma2:2b (8/12, faithfulness melhorou)
app/
  main.py                       interface Streamlit
  README.md                      instruções de execução
docs/
  relatorio_rag.md              detalhamento técnico do pipeline RAG
  gerar_relatorio_evolucao_sprint04.py  gera o PDF abaixo
  relatorio_evolucao_sprint04.pdf        relatório de evolução da Sprint 04 (separado do da Sprint 03)
demo_bonus_multiprovider_rag.py   demonstração do bônus multi-provider no RAG
equipe_sprint04.txt              nome, RM, turma e tarefa principal de cada integrante (Sprint 04)
```

### Como rodar (Sprint 04)

```bash
pip install -r requirements.txt   # inclui chromadb, langchain-chroma, pymupdf, streamlit, ragas

ollama serve
ollama pull nomic-embed-text

# 1. Adicionar PDFs em data/knowledge_base/ (ver data/knowledge_base/README.md)
# 2. Indexar
python -m src.rag.indexar

# 3. Rodar o eval do RAG (ajustar evals/eval_set_rag.json aos PDFs reais antes)
python evals/run_eval_rag.py v1

# 4. Rodar a interface
streamlit run app/main.py

# 5. Regenerar o relatório de evolução da Sprint 04 em PDF
python docs/gerar_relatorio_evolucao_sprint04.py
```
