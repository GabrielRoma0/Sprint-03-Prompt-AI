# Interface web — Sprint 04

Streamlit consumindo o pipeline RAG (`src/rag/`), com citação de fonte
visível na resposta.

## Como rodar

```bash
pip install -r requirements.txt
ollama serve
ollama pull nomic-embed-text
ollama pull llama3.1:8b   # ou o modelo definido em EVCHALLENGE_MODEL

# 1. Indexar a base de conhecimento (uma vez, ou sempre que os PDFs mudarem)
python -m src.rag.indexar

# 2. Subir a interface
streamlit run app/main.py
```

A interface abre em `http://localhost:8501`. Cada pergunta passa pelos
guardrails de `src/guardrails/` antes de chegar à chain RAG; respostas
fora do contexto disponível são sinalizadas em vez de inventadas.
