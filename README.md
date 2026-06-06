# RAG Project Guide (Onboarding + Runbook)

This document explains the `RAG` folder structure, how the project works, how to run it on a new machine, and what issues were faced (with root cause and fixes).

## 1. What This Project Does

This project has **two modes**:

1. **Direct RAG chat (no queue)**
- Script: `chat.py`
- Reads from an existing Qdrant collection and answers questions.

2. **Queued RAG API (FastAPI + RQ + Valkey/Redis)**
- API: `rag_queue/server.py`
- Background worker: `rag_queue/queue/run_worker.py`
- Job function: `rag_queue/queue/worker.py`
- Queue backend: Valkey container (`rag_queue/docker-compose.yml`)

There is also an indexing script:
- `docload.py` to load `Tutorial_EDIT.pdf`, split content, embed, and push to Qdrant.

## 2. Important Folder Structure

```text
RAG/
  .env
  requirement.txt
  docker-compose.yml                  # Qdrant container
  docload.py                          # Creates/loads vectors into Qdrant collection
  chat.py                             # Direct interactive RAG chat
  Tutorial_EDIT.pdf                   # Source doc used by docload.py
  rag_queue/
    main.py                           # Starts FastAPI app
    server.py                         # /chat and /response endpoints
    docker-compose.yml                # Valkey container for queue
    client/
      rq_client.py                    # Queue connection object
    queue/
      worker.py                       # process_query job function
      run_worker.py                   # Starts RQ SimpleWorker
      view_queued_jobs.py             # Utility script to inspect jobs
```

Notes:
- `venv/` is a local environment and should not be treated as source code.
- `__pycache__/` folders are generated artifacts.

## 3. Prerequisites

1. Python 3.11+ (project currently runs on 3.13 in your environment).
2. Docker Desktop (for Qdrant and Valkey containers).
3. Internet access for embedding and LLM calls.
4. Valid Google/Gemini API key.

## 4. Environment Setup (New Machine)

From `RAG` folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirement.txt
```

Create `.env` in `RAG/` (if not already present):

```env
GEMINI_API_KEY=your_api_key_here
```

## 5. Start Infrastructure

### 5.1 Start Qdrant (vector DB)

From `RAG/`:

```powershell
docker compose up -d
```

This uses `RAG/docker-compose.yml` and exposes Qdrant at:
- `http://localhost:6333`

### 5.2 Start Valkey (queue backend)

From `RAG/rag_queue/`:

```powershell
docker compose up -d
```

This uses `RAG/rag_queue/docker-compose.yml` and maps:
- host `6444` -> container `6379`

## 6. Index Documents into Qdrant

From `RAG/` (venv active):

```powershell
python .\docload.py
```

What it does:
1. Loads `Tutorial_EDIT.pdf`
2. Splits into chunks
3. Generates embeddings (`models/gemini-embedding-2`)
4. Creates collection (`beginner_python`)
5. Stores vectors in Qdrant

## 7. Run the Queued API Flow

You need **three running processes**.

### Terminal A: FastAPI app
From `RAG/`:

```powershell
python -m rag_queue.main
```

API runs on `http://localhost:8000`

### Terminal B: RQ worker
From `RAG/rag_queue/queue/`:

```powershell
python .\run_worker.py
```

### Terminal C: Client calls
Example enqueue request:

```http
POST http://localhost:8000/chat?query=what%20is%20natural%20disaster
```

Response gives `job_id`.

Then poll result:

```http
GET http://localhost:8000/response?job_id=<job_id>
```

Possible statuses from `/response`:
- `queued` / `started` / etc. with `result: null`
- `finished` with `result: "..."`
- `failed` with `error: "...traceback..."`

## 8. Run Direct Chat Script (Without Queue)

From `RAG/`:

```powershell
python .\chat.py
```

Type questions in terminal. Type `exit` to stop.

## 9. Issue Log: Problems Faced, Root Cause, Fix

### Issue 1: `TypeError: Client.__init__() got an unexpected keyword argument 'client'`

Where seen:
- In `rag_queue/queue/worker.py` during vector store setup.

Root cause:
- `QdrantVectorStore.from_existing_collection(...)` in installed `langchain_qdrant` version does not support passing an initialized `client=` in that method call path; extra kwargs were forwarded incorrectly.

Fix chosen:
- Use supported args for `from_existing_collection` (`url=...`) or instantiate `QdrantVectorStore(...)` with `client=` directly.
- Current worker code uses `url=` with `from_existing_collection`.

### Issue 2: `Connection closed by server` while enqueueing jobs

Where seen:
- `/chat` endpoint when `queue.enqueue(...)` was called.

Root cause:
- Valkey Docker port mapping mismatch and protocol/connection mismatch path.

Fix chosen:
- Valkey compose set to `6444:6379` (host to container default Redis port).
- Queue client points to `localhost:6444`.

### Issue 3: `Error 10061 connecting to localhost:6379`

Where seen:
- Running `rq worker` command directly.

Root cause:
- `rq worker` CLI defaults to Redis `localhost:6379` unless URL is provided.
- Project backend is on host port `6444`.

Fix chosen:
- Use `python .\run_worker.py` (already configured) OR run CLI as:
  - `rq worker --url redis://localhost:6444/0`

### Issue 4: `ValueError: Invalid attribute name: rag_queue.queue.worker.process_query`

Where seen:
- Worker execution of queued job.

Root cause:
- Worker was started from `rag_queue/queue` context; RQ could not import module path `rag_queue.queue.worker` because project root wasn’t in `sys.path`.

Fix chosen:
- In `run_worker.py`, prepend project root to `sys.path` before starting worker.

### Issue 5: Jobs not visible in queue inspection script

Where seen:
- `view_queued_jobs.py` printing no jobs.

Root cause:
- Queue name mismatch: producer enqueued to default queue, script was checking a different queue name.

Fix chosen:
- Inspect the same queue name (`default`) as producer.

### Issue 6: `/response` returned empty `{}` instead of job output

Where seen:
- `server.py` result endpoint.

Root cause:
- Accessed `job.return_value` as if it were a property in response payload; in this RQ version it is a method (`job.return_value(...)`). Method objects serialize as `{}` in FastAPI JSON output.

Fix chosen:
- Call `job.return_value(refresh=True)` and return status-aware responses (`finished`, `failed`, pending states).

## 10. Operational Notes

1. Start order matters:
- Qdrant + Valkey first
- API next
- Worker next
- Then call `/chat` and `/response`

2. If `/response` stays `queued` forever:
- Worker is not running, wrong queue name, or cannot import function.

3. If `/response` is `failed`:
- Check returned traceback in `error` field and worker terminal logs.

4. If queue jobs are missing:
- Confirm both producer and worker/scripts use same Redis host/port and same queue name.

## 11. Quick Run Checklist

1. `RAG/`: activate venv
2. `RAG/`: `docker compose up -d` (Qdrant)
3. `RAG/rag_queue/`: `docker compose up -d` (Valkey)
4. `RAG/`: `python .\docload.py` (if vectors not indexed)
5. Terminal A: `python -m rag_queue.main`
6. Terminal B: `python .\run_worker.py` (from `rag_queue/queue`)
7. POST `/chat?query=...`
8. GET `/response?job_id=...`

## 12. Suggested Next Improvements

1. Add one centralized config module for all host/port/env values.
2. Add a health endpoint checking Qdrant + Valkey + queue reachability.
3. Add a script to start all required services/commands in one step.
4. Add unit tests for `/chat` and `/response` status transitions.
