# Checklist final de entrega — Sprint 03

Atualizado em 2026-09-20 depois de rodar tudo de verdade localmente
(Ollama com `llama3.1:8b`/`gemma2:2b`, ver `docs/relatorio_modelos.md`
para por que esses modelos substituem `gpt-oss:120b`/`qwen3:8b`, incluindo
a avaliação e descarte deliberado do Ollama Cloud) e publicar no GitHub.

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
| System prompt versionado + tabela de versões | Concluído — 3 versões, tokens medidos com tiktoken | `prompts/versoes.md` |
| Relatório de uso de modelos (2+ modelos, parâmetros) | Concluído — comparação real rodada e documentada | `docs/relatorio_modelos.md` |
| Segurança e guardrails | Concluído — testado e funcionando (6/6 casos) | `src/guardrails/`, `demo_etapa2_guardrails.py` |
| Relatório de evolução (até 5 páginas) | Concluído — 4 páginas, tabela antes/depois preenchida | `docs/relatorio_evolucao.pdf` |
| Bônus multi-provider (+1) | Concluído — implementado e testado (3/3 combinações) | `src/chain/multi_provider.py` |
| Tarefa principal de cada integrante | Concluído — `equipe.txt` e seção 5 do PDF preenchidos | `equipe.txt`, `docs/relatorio_evolucao.pdf` |

Nenhum item de conteúdo obrigatório está pendente.

## 3. Como reproduzir com os modelos do enunciado (opcional, ganho marginal)

Só faz sentido em uma máquina com pelo menos ~70 GB de RAM/VRAM
disponíveis — não é o caso da máquina usada para validar esta entrega
(ver `docs/relatorio_modelos.md`).

```bash
ollama pull gpt-oss:120b
ollama pull qwen3:8b
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python evals/run_eval.py
EVCHALLENGE_MODEL=gpt-oss:120b EVCHALLENGE_MODEL_SECUNDARIO=qwen3:8b python docs/comparar_modelos.py
```

Isso reescreve `evals/sprint3_results.json` e `docs/comparacao_modelos_resultado.json`
com os modelos originais — atualizar `docs/relatorio_modelos.md` e reexecutar
`docs/gerar_relatorio_evolucao.py` depois.

## 4. Condições de entrega (§10 do enunciado)

- [x] Histórico Git com commits organizados por área (schemas, prompts, chain,
      guardrails, demos, evals, docs) — não um commit único
- [x] Nenhuma API key no histórico do Git (`git log -p` conferido)
- [x] Repositório público no GitHub: https://github.com/GabrielRoma0/Sprint-03-Prompt-AI
- [x] `equipe.txt` preenchido (nome, RM, turma e função de cada integrante)
- [x] `docs/relatorio_evolucao.pdf` (4 de 5 páginas) incluído no repositório
- [ ] Adicionar o professor como colaborador do repositório (ou confirmar que o
      acesso público já é suficiente) e submeter o link pelo canal da disciplina

## 5. Integridade acadêmica (§11)

- [ ] Confirmar que o repositório é original do grupo (não reaproveitado de outro grupo/semestre)
- [ ] Nenhum uso de conteúdo de outra disciplina sem autorização (auto-plágio)
