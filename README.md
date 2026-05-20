# Prompt Master

> **MVP** — This README documents the current state of the project as of the MVP release. All future features and changes beyond this point are considered post-MVP work.

A tool for engineers building RAG and agentic systems. You paste a prompt, answer a few clarifying questions, and receive an expert rewrite of that prompt backed by a curated knowledge base. The rewrite comes with a plain-language explanation of every change made and why.

The system is not a general-purpose chatbot. It is a focused, three-step pipeline — clarify, retrieve, synthesize — designed specifically around the task of improving prompts for AI systems.

---

## File Structure

```
prompt-master/
│
├── backend/
│   ├── agents/
│   │   ├── base.py                   # Anthropic client factory, shared agent setup
│   │   ├── question_agent.py         # Stage 1 — generates clarifying questions from the raw prompt
│   │   ├── reformulation_agent.py    # Stage 2 — turns prompt + answers into a structured vector query
│   │   └── synthesizer_agent.py      # Stage 3 — rewrites the prompt using retrieved docs + clarifications
│   │
│   ├── rag/
│   │   ├── chunker.py                # Token-bounded text splitting (cl100k_base, 512 tokens, 64 overlap)
│   │   ├── embedder.py               # OpenAI embeddings API wrapper (text-embedding-3-small, 1536 dims)
│   │   └── retriever.py              # Two-stage retrieval: metadata filter then cosine similarity ranking
│   │
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy Document model — stores chunks, tags, and embeddings
│   │   └── engine.py                 # Async SQLAlchemy engine and session factory
│   │
│   ├── schemas/
│   │   ├── agents/                   # Pydantic I/O schemas for each agent (question, reformulation, synthesizer)
│   │   └── api/                      # Pydantic request/response schemas for the HTTP layer
│   │
│   ├── services/
│   │   └── session_service.py        # Orchestrates the full pipeline — wires agents, embedder, retriever
│   │
│   ├── api/v1/
│   │   ├── router.py                 # v1 API router
│   │   └── endpoints/session.py      # /session/start and /session/respond HTTP endpoints
│   │
│   ├── config.py                     # All settings loaded from .env (models, DB URL, RAG params)
│   └── main.py                       # FastAPI app factory, CORS middleware, lifespan
│
├── scripts/
│   ├── taxonomy_discovery.py         # Offline — uses Claude to discover categories and tags from raw corpus
│   └── ingest.py                     # Offline — chunks, tags with Claude, embeds with OpenAI, writes to pgvector
│
├── corpus/                           # Source documents for the knowledge base (.md files)
│   ├── claude-streaming-messages.md
│   ├── claude-structured-output.md
│   └── claude-tool-use.md
│
├── alembic/versions/0001_initial.py  # Initial DB migration — enables pgvector, creates documents table
├── taxonomy.json                     # Single source of truth for all RAG categories and concept tags
├── docker-compose.yml                # Runs the pgvector database only (backend runs locally)
└── pyproject.toml                    # Python project config and dependencies
```

---

## Strategies

### Three-agent pipeline

The session flow is broken into three discrete agents, each with a single responsibility. No agent does more than one thing. The pipeline is orchestrated in `session_service.py`, which is the only place where the agents, embedder, and retriever are wired together — the HTTP layer (`session.py`) has no knowledge of how the pipeline works.

### Forced structured output via tool use

Every agent uses Claude's tool use API with `tool_choice: { type: "tool" }` to force a specific tool call. This guarantees that LLM responses are always validated Pydantic models — there is no free-text parsing anywhere in the pipeline. Each agent defines its output schema directly from its Pydantic model via `model_json_schema()`.

### Taxonomy-constrained retrieval

The knowledge base is organized using a taxonomy (`taxonomy.json`) of categories and concept tags. At ingest time, Claude classifies each chunk against the taxonomy. At query time, the reformulation agent is given the same taxonomy and is constrained to output only values from it. The retriever then uses those values for a hard metadata filter (B-tree on category, GIN index on concept_tags) before applying cosine similarity ranking. This two-stage retrieval avoids searching across unrelated documents and keeps results precise.

### Token-aligned chunking

The chunker uses the same tokenizer as the embedding model (`cl100k_base`) to split documents by token count rather than character count. Chunk size (512 tokens) and overlap (64 tokens) are configurable via settings. This avoids the common bug where character-based chunking produces variable-density embedding inputs.

### Separation of embedding and generation models

Embeddings are produced by OpenAI (`text-embedding-3-small`) while all generation calls go to Anthropic Claude (`claude-sonnet-4-6`). The two are kept completely separate — the embedder has no dependency on the agent code and vice versa. This makes it straightforward to swap either model independently.

### Observability via Langfuse

All LLM calls are decorated with `@observe` from Langfuse. Each agent separates the observable generation call (`_call_claude`) from its public `run` function, giving a clean two-level trace: the agent span wraps the generation span. This makes it easy to inspect inputs, outputs, latency, and token counts for every step of a session.
