# Base de conhecimento — Sprint 04

4 PDFs (§5 do enunciado):

- `manual_chargegrid_evchargeops.pdf` — manual de produto GoodWe ChargeGrid / EV ChargeOps
- `regimento_carregamento_compartilhado.pdf` — regimento condominial de carregamento compartilhado
- `faq_carregamento.pdf` — FAQ de carregamento
- `tabela_tarifaria.pdf` — tabela tarifária

## Origem dos documentos

São documentos **sintéticos**: o grupo não teve acesso a manuais/
regimentos/tarifários oficiais da GoodWe Brasil, então escreveu conteúdo
plausível e consistente com o domínio do projeto (mesmos enums/faixas de
`src/schemas/consulta_recarga.py`: estados do carregador, potência até 22
kW AC, etc.) para alimentar o pipeline RAG. Cada PDF traz esse aviso
explícito na primeira página — não são reproduções nem paráfrases de
nenhum material real do fabricante.

Gerados por `_gerar_pdfs_sinteticos.py` (reportlab), nesta mesma pasta.
Para regenerar (ex.: depois de editar o conteúdo):

```bash
python data/knowledge_base/_gerar_pdfs_sinteticos.py
```

Esse script **não** é indexado — `src/rag/loader.py` varre só `*.pdf`
neste diretório.

## Trocar por documentos reais

Se o grupo conseguir acesso a documentação oficial da GoodWe antes da
entrega, o processo é só substituir os PDFs aqui (mesmo nome de arquivo ou
não — `loader.py` indexa qualquer `*.pdf` da pasta) e reindexar. Nesse
caso, remover o aviso de "documento sintético" deixa de ser necessário e
`docs/relatorio_rag.md`/`eval_set_rag.json` devem ser atualizados para
refletir o conteúdo real.

## Indexar

```bash
python -m src.rag.indexar
```

Isso popula `data/chroma_db/` (gitignored — não versionar o índice, só os
PDFs de origem e o código que os gera).
