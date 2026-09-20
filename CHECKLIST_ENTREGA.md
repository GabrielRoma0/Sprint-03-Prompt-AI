# Checklist final de entrega — Sprint 03

Atualizado em 2026-09-20 depois de rodar tudo de verdade localmente
(Ollama com `llama3.1:8b`/`gemma2:2b`, ver `docs/relatorio_modelos.md`
para por que esses modelos substituem `gpt-oss:120b`/`qwen3:8b`).

## 1. Estrutura de pastas (§5 do enunciado)

- [x] `prompts/` — system_prompt_v1.md, v2.md, v3.md, versoes.md, medir_tokens.py
- [x] `src/chain/` — builder.py, memoria.py, guarded_chain.py, multi_provider.py (bônus)
- [x] `src/schemas/` — consulta_recarga.py
- [x] `src/guardrails/` — scope_validator.py, moderation.py
- [x] `evals/` — eval_set.json, run_eval.py, sprint3_results.json
- [x] `docs/` — relatorio_modelos.md, relatorio_evolucao.pdf, gerar_relatorio_evolucao.py, comparar_modelos.py

## 2. Pontos obrigatórios (§6) — status

| Item | Status | Onde |
|---|---|---|
| System prompt versionado + tabela de versões | ✅ 3 versões, tokens medidos com tiktoken | `prompts/versoes.md` |
| Relatório de uso de modelos (2+ modelos, parâmetros) | ✅ Comparação real rodada e documentada | `docs/relatorio_modelos.md` |
| Segurança e guardrails | ✅ Testado e funcionando (6/6 casos) | `src/guardrails/`, `demo_etapa2_guardrails.py` |
| Relatório de evolução (até 5 páginas) | ✅ 3 páginas, tabela antes/depois preenchida | `docs/relatorio_evolucao.pdf` |
| Bônus multi-provider (+1) | ✅ Implementado e testado (3/3 combinações) | `src/chain/multi_provider.py` |

## 3. Único item que ainda depende de vocês

- [ ] **Tarefa principal de cada integrante** em `equipe.txt` (nomes/RM/turma já
      preenchidos) — depois de preencher, rodar `python docs/gerar_relatorio_evolucao.py`
      de novo para atualizar a tabela da seção 5 do PDF.

## 4. Como reproduzir com os modelos do enunciado (se quiserem antes de entregar)

```bash
ollama pull gpt-oss:120b   # ~120B params — avaliar se cabe no hardware/tempo disponível
ollama pull qwen3:8b
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python evals/run_eval.py
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python docs/comparar_modelos.py
```

Isso reescreve `evals/sprint3_results.json` e `docs/comparacao_modelos_resultado.json`
com os modelos originais — atualizar `docs/relatorio_modelos.md` e reexecutar
`docs/gerar_relatorio_evolucao.py` depois.

## 5. Condições de entrega (§10 do enunciado)

- [x] Histórico Git com commits organizados por área (schemas, prompts, chain,
      guardrails, demos, evals, docs) — não um commit único
- [x] Nenhuma API key no histórico do Git (`git log -p` conferido)
- [ ] Repositório público no GitHub com acesso ao professor (fazer `git push` para
      o repositório remoto do grupo)
- [ ] Entrega por link do repositório + `equipe.txt` preenchido (falta só a
      tarefa principal — ver item 3)
- [x] `docs/relatorio_evolucao.pdf` (3 de 5 páginas) incluído no repositório

## 6. Integridade acadêmica (§11)

- [ ] Confirmar que o repositório é original do grupo (não reaproveitado de outro grupo/semestre)
- [ ] Nenhum uso de conteúdo de outra disciplina sem autorização (auto-plágio)
