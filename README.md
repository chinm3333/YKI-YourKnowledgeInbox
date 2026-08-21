# AI Knowledge Inbox

Single-user web app: save notes and URLs, then ask questions over them with a small RAG pipeline.

- **LLM:** Groq (`openai/gpt-oss-20b`)
- **Embeddings:** local `all-MiniLM-L6-v2`
- **Items store:** SQLite
- **Vectors:** Chroma persisted under `backend/chroma_data`

## Run

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Test
```bash
pytest -v
```

Put your Groq key in `.env` as `GROQ_API_KEY`. First ingest downloads the MiniLM model (one-time).

```bash
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/ingest`, `/items`, and `/query` to the API.

### Tests

```bash
cd backend
pytest
```

API tests mock Chroma so they stay fast (no MiniLM download).

## API

| Method | Path | Body | Success |
|---|---|---|---|
| POST | `/ingest` | `{ "type": "note" \| "url", "content": "..." }` | `201` item + `chunk_count` |
| GET | `/items` | — | `{ "items": [...] }` |
| DELETE | `/items/{id}` | — | `204` |
| POST | `/query` | `{ "question": "...", "top_k": 5 }` | `{ "answer", "sources" }` |

Errors: `{ "error", "detail" }` with `400` validation/SSRF, `404` missing item, `422` fetch/extract, `502` embedding/LLM, `500` unexpected.

## Design notes (interview)

**Chunking.** Sliding windows (~700 chars, 100 overlap) that prefer paragraph, then newline, then sentence, then space. Overlap so a fact that straddles a window is still retrievable. Token splitters are nicer at scale; they are not needed for short notes.

**Two stores.** SQLite is the source of truth for listing and citations. Chroma only holds chunk vectors plus `item_id` metadata. A vector DB alone makes “show my inbox” awkward.

**Ingest consistency.** Chunk first. Write vectors, then SQLite. If SQLite fails, delete the Chroma ids so the inbox never lists an unsearchable item.

**URL fetch.** Timeout, size cap, and an SSRF check (no localhost/private/link-local IPs). Redirects are followed one hop at a time and re-checked.

**Retrieval floor.** Chunks below `min_chunk_score` (default `0.15`) are dropped so the LLM is not stuffed with noise. Tune if MiniLM distances look off for your corpus.

**What breaks first.** Sync URL fetch on the request thread, in-process MiniLM, local Chroma (one process, folder persistence), no hybrid keyword search, Llama context if `top_k` is too high.

**Production.** Queue ingest, Postgres + pgvector, better HTML extraction, auth, rate limits, retrieval eval, request tracing. Keep the same API shape.

<img width="1905" height="908" alt="{8F9EAA92-E4C2-4913-A7B5-40E081AF3E1E}" src="https://github.com/user-attachments/assets/955d19e0-7e60-4c33-8ee4-de8aec70f485" />
