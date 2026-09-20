# Checklist final de entrega — Sprint 03

## 1. Estrutura de pastas (§5 do enunciado)

- [x] `prompts/` — system_prompt_v1.md, v2.md, versoes.md, medir_tokens.py
- [x] `src/chain/` — builder.py, memoria.py, guarded_chain.py, multi_provider.py (bônus)
- [x] `src/schemas/` — consulta_recarga.py
- [x] `src/guardrails/` — scope_validator.py, moderation.py
- [x] `evals/` — eval_set.json, run_eval.py, sprint3_results.json
- [x] `docs/` — relatorio_modelos.md, relatorio_evolucao.pdf, gerar_relatorio_evolucao.py

## 2. Pontos obrigatórios (§6) — status

| Item | Status | Onde |
|---|---|---|
| System prompt versionado + tabela de versões | ⚠️ Falta preencher tokens reais | `prompts/versoes.md` |
| Relatório de uso de modelos (2+ modelos, parâmetros) | ⚠️ Falta rodar com Ollama e preencher números | `docs/relatorio_modelos.md` |
| Segurança e guardrails | ✅ Testado e funcionando (5/5 casos) | `src/guardrails/`, `demo_etapa2_guardrails.py` |
| Relatório de evolução (até 5 páginas) | ⚠️ Falta preencher `[PREENCHER]` | `docs/relatorio_evolucao.pdf` |
| Bônus multi-provider (+1) | ✅ Implementado | `src/chain/multi_provider.py` |

## 3. Antes de rodar localmente

- [ ] `pip install -r requirements.txt`
- [ ] `pip install tiktoken --break-system-packages` (para `prompts/medir_tokens.py`)
- [ ] Ollama instalado e rodando: `ollama serve`
- [ ] Modelos baixados: `ollama pull gpt-oss:120b` e `ollama pull qwen3:8b`
- [ ] Copiar `.env.example` para `.env` e preencher (não commitar `.env`)

## 4. Pendências para completar o conteúdo (todas com script pronto)

- [ ] Rodar `python prompts/medir_tokens.py` → preencher `prompts/versoes.md`
- [ ] Rodar `python evals/run_eval.py` com os 6 casos LLM habilitados → atualizar `evals/sprint3_results.json`
- [ ] Rodar comparação de modelos (script em `docs/relatorio_modelos.md`) → preencher a tabela de resultados
- [ ] Editar `docs/gerar_relatorio_evolucao.py` (baseline Sprints 1/2, terceiro problema, equipe) → rodar de novo para regenerar o PDF
- [ ] Preencher `equipe.txt` com nome, RM e turma reais
- [ ] Rodar `python demo_bonus_multiprovider.py` e, se quiser, anexar a saída como evidência extra no relatório

## 5. Condições de entrega (§10 do enunciado)

- [ ] Repositório público com acesso ao professor
- [ ] Histórico Git com commits regulares de cada integrante (não um commit único no fim)
- [ ] Nenhuma API key no histórico do Git — `.gitignore` já protege `.env`; conferir `git log -p` antes de entregar
- [ ] Entrega por link do repositório + `equipe.txt` preenchido
- [ ] `docs/relatorio_evolucao.pdf` (até 5 páginas) incluído no repositório

## 6. Integridade acadêmica (§11)

- [ ] Confirmar que o repositório é original do grupo (não reaproveitado de outro grupo/semestre)
- [ ] Nenhum uso de conteúdo de outra disciplina sem autorização (auto-plágio)
