# YouTube Transcript Chatbot

A local development starter for a web-based RAG app. Users can paste a YouTube link, paste/upload a transcript, ask questions, and get answers grounded in retrieved transcript chunks.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- LLM: Hugging Face Inference Providers
- Indexing: LangChain `RecursiveCharacterTextSplitter`
- Vector store: FAISS
- Retriever: LangChain similarity retriever with `k=4`
- Embeddings: Hugging Face by default, OpenAI optional
- Future storage: PostgreSQL with pgvector

## Folder Layout

```txt
apps/
  api/       FastAPI backend
  web/       Next.js frontend
```

## Local Setup

### 1. Backend

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at:

```txt
http://localhost:8000
```

API docs:

```txt
http://localhost:8000/docs
```

### 2. Frontend

Open a second terminal:

```powershell
cd "C:\Users\Lokesh Naidu SP\Documents\New project"
npm.cmd install
Copy-Item apps\web\.env.local.example apps\web\.env.local
npm.cmd run dev:web
```

Frontend runs at:

```txt
http://localhost:3000
```

## Hugging Face

Create a Hugging Face token and add it to `apps/api/.env`:

```env
HF_TOKEN=your_token_here
HF_MODEL=openai/gpt-oss-120b:fastest
```

Without `HF_TOKEN`, the backend still runs and returns a simple extractive answer from the retrieved transcript chunks.

## Embeddings

The default embedding provider is free/local Hugging Face embeddings:

```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

To use OpenAI embeddings instead:

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Windows Notes

If `python` is not recognized, install Python 3.11+ from python.org and enable "Add python.exe to PATH" during setup.

If PowerShell blocks `npm`, use `npm.cmd` as shown above.

## Optional Database

For later PostgreSQL + pgvector development:

```powershell
docker compose up -d
```
