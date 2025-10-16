# Knowledge Base Search Engine — Gemini Edition (Ready-to-Run)

A Retrieval-Augmented Generation (RAG) app that lets you upload PDFs and ask questions.
This edition uses **Google Gemini (free API)** for answering with retrieved context.

## Quick Start

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="YOUR_FREE_GEMINI_KEY"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000/frontend

## What’s inside

- FastAPI backend (RAG pipeline with ChromaDB + SentenceTransformers)
- Gemini LLM integration (`app/services/llm_service.py`)
- PDF text extraction & chunking
- Frontend UI in `/frontend`
- Reuses your existing Chroma DB if placed in `/chroma`

## Notes
- Set `GEMINI_API_KEY` in your environment before running.
- To reset vector DB, delete the `/chroma` folder and re-upload PDFs.
- Default model: `gemini-1.5-flash` (change in `llm_service.py` if desired).
