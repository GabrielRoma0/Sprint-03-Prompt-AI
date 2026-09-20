# EV Challenge — GoodWe — Sprint 03

Disciplina Prompt and Artificial Intelligence — FIAP, Ciência da Computação,
turma 1CCR, semestre 2026.2. Parceiro: GoodWe Brasil.

Este repositório é a Sprint 03 do projeto EV Challenge GoodWe, dando
continuidade ao chatbot desenvolvido nas Sprints 1 e 2 do semestre
anterior. O objetivo desta etapa foi reconstruir o núcleo conversacional
do chatbot usando a stack do Módulo 1 da disciplina (LangChain LCEL,
memória conversacional, structured output com Pydantic v2 e context
engineering), mantendo a inferência 100% local via Ollama, sem uso de
nenhuma API paga.

## Equipe

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

## Contexto do projeto

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

## O que foi implementado

### Chain LCEL e memória por sessão

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

### Structured output com Pydantic v2

`src/schemas/consulta_recarga.py` define o schema `ConsultaRecarga`, que
toda resposta do chatbot precisa satisfazer: estado do carregador (enum),
potência instantânea, energia entregue, valor faturado e uma observação
opcional. Cada campo numérico tem um `field_validator` que rejeita
valores fora da faixa esperada (ex.: potência negativa, ou acima do
catálogo GoodWe). O campo de potência é o único opcional do schema: ele
começou como obrigatório, mas o eval mostrou que isso forçava o modelo a
inventar um número quando a conversa não informava a potência — tornado
opcional, o modelo passou a responder `null` nesse caso, como esperado.

### Context engineering e prompt versionado

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

### Guardrails de segurança e escopo

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

### Eval reexecutado

`evals/eval_set.json` reúne 11 casos de teste cobrindo os mesmos tipos de
cenário usados nas Sprints 1 e 2: 3 casos de happy path, 3 de edge case,
2 de tentativa de jailbreak e 3 de pedido fora de escopo. O script
`evals/run_eval.py` reexecuta todos os casos contra a versão atual do
chatbot (guardrails, quando aplicável, mais a chain completa com memória),
com checagem automática de critério quando o critério é objetivo (ex.:
estado do carregador bate com o esperado) e sinalização de revisão manual
quando o critério é qualitativo. Resultado registrado em
`evals/sprint3_results.json`: 11 de 11 casos aprovados.

### Comparação de modelos e bônus multi-provider

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

### Relatório de evolução do projeto

`docs/relatorio_evolucao.pdf` (gerado por
`docs/gerar_relatorio_evolucao.py`) reúne o resumo da evolução desde as
Sprints 1/2, as decisões técnicas da refatoração, a tabela obrigatória de
comparativo antes/depois (qualidade das respostas, tokens por turno,
latência, acurácia do structured output, casos de jailbreak e
out-of-scope bloqueados), cinco problemas encontrados durante o
desenvolvimento com a decisão tomada para cada um, e a divisão de
trabalho da equipe.

## Estrutura do repositório

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

## Como rodar

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

## Resultados

- Eval reexecutado: 11 de 11 casos aprovados (`evals/sprint3_results.json`).
- Guardrails: 6 de 6 casos corretos (`demo_etapa2_guardrails.py`).
- Comparação de modelos: `llama3.1:8b` com 5/6 no eval e latência média de
  20,2 s; `gemma2:2b` com 4/6 e 21,9 s (`docs/comparacao_modelos_resultado.json`).
- Bônus multi-provider: 3 de 3 combinações de modelo/prompt testadas.
