# Tabela de versões — system prompt

Ganho medido com `prompts/medir_tokens.py` (codificação `cl100k_base`, usada
como proxy consistente de contagem entre versões). Medido em 2026-09-20.

| Versão | O que mudou | Por quê | Tokens (cl100k_base) | Variação vs. anterior |
|---|---|---|---|---|
| v1 | Prompt inicial com tags básicas: `<role>`, `<scope>`, `<restrictions>`, `<output_format>`. | Validar rapidamente a chain LCEL da Etapa 1 com um prompt mínimo funcional. | 310 | — |
| v2 | Adiciona `<security>` (defesa explícita contra jailbreak/prompt injection), `<refusal_examples>` (exemplos de recusa) e regra explícita para não inventar valores de campos ainda não mencionados. | Testes manuais mostraram o modelo aceitando instruções embutidas no texto do usuário e "alucinando" valores de energia/faturamento quando o usuário não os informava. `<security>` e a regra de "não inventar" atacam esses dois problemas diretamente. | 619 | +309 (quase dobrou) |
| v3 | `<output_format>` passa a citar `potencia_kw` explicitamente como o único campo que deve virar `null` quando não informado (os demais campos numéricos continuam com default `0.0`), e esclarece que perguntas sobre valor já faturado de uma sessão não são aconselhamento financeiro. Acompanha a mudança do schema (`potencia_kw` virou opcional, default `null`, em `src/schemas/consulta_recarga.py`). | Duas falhas reais encontradas pelo eval reexecutado (`evals/sprint3_results.json`): (1) casos `ec-01`/`ec-03` mostraram o modelo inventando `potencia_kw` porque o schema tornava esse campo obrigatório; (2) uma primeira versão da instrução ("todo campo numérico vira null") quebrou `hp-01`/`hp-02` porque generalizou demais e o modelo tentou zerar campos que o schema não permite serem `null`; e casos envolvendo "valor faturado" foram recusados por engano como se fossem pergunta financeira. v3 corrige as duas coisas: instrução restrita só a `potencia_kw`, e uma frase explícita desambiguando "faturamento de sessão" vs. "aconselhamento financeiro". | 834 | +215 |

O aumento de tokens em v2 é um trade-off deliberado: mais contexto de
segurança por turno (custo maior por chamada ao LLM) em troca de bloquear
duas classes de falha observadas em teste manual com v1 (jailbreak não
recusado e alucinação de campos numéricos). v3 é um refinamento mais
barato (+164 tokens) e mais específico, direcionado a uma falha real
encontrada pelo eval (não por teste manual) — ver "Problemas encontrados
e soluções" em `docs/relatorio_evolucao.pdf` para o antes/depois medido
com `evals/run_eval.py`.

## Como preencher

1. Rode `python prompts/medir_tokens.py` (após `pip install tiktoken`).
2. Copie os valores impressos para as colunas "Tokens" e "Variação".
3. Se criar uma v3, adicione uma nova linha nesta tabela — nunca sobrescreva
   uma versão anterior, o histórico completo é parte da evidência exigida
   pelo Bloco B da rubrica.

## Critério de "ganho"

Este documento mede **tamanho/custo do prompt** (tokens). O ganho de
**qualidade** de cada versão (respostas corretas, guardrails funcionando)
deve ser demonstrado pelo eval set reexecutado na Etapa 3
(`evals/sprint3_results.json`) e consolidado na tabela antes/depois do
relatório de evolução (`docs/relatorio_evolucao.pdf`).
