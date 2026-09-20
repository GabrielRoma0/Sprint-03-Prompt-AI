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
