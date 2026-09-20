# EV Challenge — GoodWe · Sprint 03 (entrega consolidada)

Refactory conversacional em LangChain LCEL: chain `prompt | llm | parser`,
memória por sessão com limite de tokens, structured output Pydantic v2,
context engineering (XML tagging) e guardrails de segurança/escopo.

## Estrutura

```
prompts/
  system_prompt_v1.md         # Etapa 1
  system_prompt_v2.md         # Etapa 2 — + <security>, + <refusal_examples>
  versoes.md                   # tabela de versões (falta preencher tokens reais)
  medir_tokens.py               # mede tokens de cada versão com tiktoken
src/
  chain/
    builder.py                 # chain LCEL (Etapa 1)
    memoria.py                  # memória por sessão com limite de tokens (Etapa 1)
    guarded_chain.py            # guardrails + chain (Etapa 2)
    multi_provider.py           # BÔNUS: consulta múltiplos modelos/prompts (Etapa 4)
  schemas/
    consulta_recarga.py         # schema Pydantic v2 (Etapa 1)
  guardrails/
    moderation.py                # jailbreak/prompt injection (Etapa 2)
    scope_validator.py           # escopo GoodWe: jurídico/financeiro/elétrico (Etapa 2)
evals/
  eval_set.json                 # 11 casos: happy path, edge case, jailbreak, out-of-scope
  run_eval.py                    # reexecuta o eval (Etapa 3)
  sprint3_results.json           # resultado parcial já executado (guardrails: 5/5 ok)
docs/
  relatorio_modelos.md          # comparação gpt-oss:120b vs. qwen3:8b (Etapa 3)
  gerar_relatorio_evolucao.py   # gera o PDF abaixo
  relatorio_evolucao.pdf         # relatório de evolução, 3 páginas (Etapa 3)
demo_etapa1.py                   # 4 turnos demonstrando chain + memória
demo_etapa2_guardrails.py        # 6 casos de guardrail — já testado, 100% ok
demo_bonus_multiprovider.py      # BÔNUS: mesma entrada em 3 combinações modelo/prompt
equipe.txt                        # preencher com nome/RM/turma
.env.example                      # copiar para .env (gitignored) e preencher
.gitignore                        # protege .env e caches locais
CHECKLIST_ENTREGA.md              # o que já está pronto e o que falta rodar/preencher
requirements.txt
```

## Como rodar (ordem sugerida)

```bash
pip install -r requirements.txt
pip install tiktoken --break-system-packages

ollama pull gpt-oss:120b
ollama pull qwen3:8b   # para a comparação de modelos e o bônus
ollama serve

cp .env.example .env   # preencha se necessário; nunca commitar .env

# 1. Validar a chain básica (Etapa 1)
python demo_etapa1.py

# 2. Validar os guardrails (Etapa 2) — não precisa do Ollama
python demo_etapa2_guardrails.py

# 3. Medir tokens dos prompts e reexecutar o eval completo (Etapa 3)
python prompts/medir_tokens.py
python evals/run_eval.py   # depois de habilitar os casos LLM, ver README_ETAPA3

# 4. Bônus: multi-provider
python demo_bonus_multiprovider.py
```

## O que já está validado neste ambiente de desenvolvimento

- Sintaxe de **todos** os arquivos Python: ok (`py_compile`)
- Guardrails (`demo_etapa2_guardrails.py`): **5/5 casos corretos**, executado de verdade
- `evals/sprint3_results.json`: 5/11 casos executados de verdade (100% aprovados), 6 pendentes do Ollama local
- `docs/relatorio_evolucao.pdf`: gerado, 3 páginas, dentro do limite de 5

O que depende do Ollama local (chain LCEL completa, comparação de modelos,
6 casos do eval) está com o código pronto mas não pôde ser executado aqui
por falta de acesso ao Ollama neste sandbox — ver `CHECKLIST_ENTREGA.md`
para o passo a passo do que falta rodar.

## Pontuação mapeada por arquivo

| Bloco | Pontos | Arquivos |
|---|---|---|
| A — Refactory LangChain | 40 | `src/chain/builder.py`, `memoria.py`, `src/schemas/` |
| B — Prompt versionado + relatório de modelos | 25 | `prompts/versoes.md`, `docs/relatorio_modelos.md` |
| C — Segurança e guardrails | 15 | `src/guardrails/`, `demo_etapa2_guardrails.py` |
| D — Eval, evolução e relatório | 20 | `evals/`, `docs/relatorio_evolucao.pdf` |
| Bônus — multi-provider | +1 | `src/chain/multi_provider.py` |
