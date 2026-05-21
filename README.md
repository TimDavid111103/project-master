# Prompt Master

> **v2** — This README documents the current state of the project as of the v2 release. The MVP produced a rewritten prompt; v2 replaces that with structured analysis across three graded dimensions, adds per-project memory, and upgrades the retrieval pipeline to an agentic loop.

A tool for engineers building RAG and agentic systems. You create a project, paste a prompt, answer a few clarifying questions, and receive a structured analysis grading your prompt across three dimensions: intent accuracy, technical language, and standards alignment. Each dimension gets a letter grade (F through S) and a specific, actionable explanation. The system gets smarter over time — it reads your project history before generating questions and before grading your prompt.

The system is not a general-purpose chatbot. It is a focused, three-step pipeline — clarify, retrieve, analyse — designed specifically around the task of evaluating and improving prompts for AI systems.

---

## File Structure

```
prompt-master/
│
├── backend/
│   ├── agents/
│   │   ├── base.py                   # Anthropic client factory, shared agent setup
│   │   ├── clarifying_agent.py       # Stage 1 — generates questions, skips repeats using project memory
│   │   ├── retrieval_agent.py        # Stage 2 — agentic loop over vector DB with five retrieval tools
│   │   └── analysis_agent.py         # Stage 3 — grades the prompt on three dimensions, no rewrite
│   │
│   ├── rag/
│   │   ├── chunker.py                # Docling-based hierarchical chunker with Claude context summaries
│   │   └── embedder.py               # OpenAI embeddings API wrapper (text-embedding-3-small, 1536 dims)
│   │
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy models — Document, Project, RawPrompt, QAPairRecord, PromptAnalysisRecord
│   │   └── engine.py                 # Async SQLAlchemy engine and session factory
│   │
│   ├── schemas/
│   │   ├── agents/
│   │   │   ├── common.py             # ClarifyingQuestion and UserAnswer — shared across agents
│   │   │   ├── clarifying.py         # ClarifyingAgentInput / ClarifyingAgentOutput
│   │   │   ├── retrieval.py          # RetrievalAgentInput / RetrievalAgentOutput / RetrievedDocResult / QAPair
│   │   │   └── analysis.py           # AnalysisAgentInput / AnalysisAgentOutput / PromptAnalysis / DimensionGrade
│   │   ├── api/
│   │   │   ├── session.py            # SessionStartRequest, SessionRespondResponse, SessionContext
│   │   │   └── projects.py           # CreateProjectRequest / CreateProjectResponse
│   │   └── memory.py                 # ProjectMemory — the context object passed into agents from memory storage
│   │
│   ├── services/
│   │   ├── session_service.py        # Orchestrates the full pipeline — wires agents and memory service
│   │   └── memory_service.py         # Reads and writes project memory; implements the threshold strategy
│   │
│   ├── api/v1/
│   │   ├── router.py                 # v1 API router
│   │   └── endpoints/
│   │       ├── session.py            # /session/start and /session/respond HTTP endpoints
│   │       └── projects.py           # /projects endpoint for creating projects
│   │
│   ├── config.py                     # All settings loaded from .env (models, DB URL, RAG params, memory threshold)
│   └── main.py                       # FastAPI app factory, CORS middleware, lifespan
│
├── scripts/
│   ├── taxonomy_discovery.py         # Offline — uses Claude to discover categories and tags from raw corpus
│   └── ingest.py                     # Offline — hierarchical chunk, tag, context-summarise, embed, write to DB
│
├── corpus/                           # Source documents for the knowledge base (.md and .pdf files)
│   ├── claude-streaming-messages.md
│   ├── claude-structured-output.md
│   └── claude-tool-use.md
│
├── alembic/versions/
│   ├── 0001_initial.py               # Enables pgvector, creates documents table with HNSW index
│   └── 0002_v2_schema.py             # Adds memory tables, hierarchical chunking columns, switches to DiskANN
├── taxonomy.json                     # Single source of truth for all RAG categories and concept tags
├── docker-compose.yml                # Runs the pgvectorscale database only (backend runs locally)
└── pyproject.toml                    # Python project config and dependencies
```

---

## Strategies

### Three-agent pipeline

The session flow is broken into three discrete agents, each with a single responsibility. The Clarifying Agent reads project memory before generating questions and suppresses any question already asked in a previous session. The Retrieval Agent runs an agentic loop over the vector DB, choosing from five tools — metadata-filtered search, parent chunk retrieval, multi-query, query expansion, and relevance checking — until it decides it has gathered enough evidence to terminate. The Prompt Analysis Agent receives the retrieved context and project history and returns a `PromptAnalysis` object: three `DimensionGrade` values, each with a letter grade and a specific explanation. No agent produces a rewritten prompt. `session_service.py` is the only place where all three agents, the memory service, and the taxonomy are wired together.

### Forced structured output via tool use

Every agent uses Claude's tool use API with `tool_choice: { type: "tool" }` to force a specific tool call on every generation call. This guarantees that LLM responses are always validated Pydantic models — there is no free-text parsing anywhere in the pipeline. Each agent defines its output schema directly from its Pydantic model via `model_json_schema()`. The Retrieval Agent extends this pattern in two directions: the five retrieval tools each have an `input_schema` generated from a dedicated Pydantic model, and `_dispatch_tool` calls `Model.model_validate(args)` on every tool invocation from Claude before executing it. This means every boundary where data crosses from the LLM into Python code is validated.

### Project memory with threshold-based context

Every project has its own isolated memory that persists raw prompts, Q&A pairs, and structured analyses across sessions. Before each pipeline run, `memory_service.load_memory` reads this history and assembles a `ProjectMemory` object that agents can use as context. Below a configurable session threshold (default 10 entries), all memory is passed directly into the agent context. Above the threshold, the current prompt is embedded and the most similar past entries are retrieved by cosine similarity from each memory table — the same two-stage pattern used for the knowledge base. Previous questions are always fetched in full regardless of the threshold, because deduplication is a hard constraint, not a context enrichment.

### Agentic retrieval with taxonomy validation

Instead of a single structured query, the Retrieval Agent drives an iterative conversation with Claude using `tool_choice: { type: "auto" }`. On each turn Claude can call one or more retrieval tools; all results are fed back as `tool_result` blocks in the same conversation; and the loop continues until Claude calls `output_retrieved_docs`. The agent is responsible for generating the taxonomy metadata (category and concept_tags) internally from the prompt and answers. The tool dispatcher validates these values against `taxonomy.json` — unknown categories are corrected and unknown tags are dropped — and the error is returned as a tool result string so Claude can self-correct on the next iteration. The loop is bounded by `MAX_ITERATIONS = 8`.

### Hierarchical chunking with contextual retrieval

Documents are parsed using Docling, which preserves headings, tables, code blocks, and lists rather than splitting blindly on token boundaries. Each document is chunked at two levels: section-level parent chunks (≈ 2048 tokens) and child chunks (≈ 512 tokens), with each child carrying a `parent_id` foreign key back to its section. At ingest time, Claude generates a one-sentence `context_summary` for each child chunk describing what it covers and where it sits in the document. This summary is prepended to the chunk content before embedding, so the vector representation reflects document position and not just the raw text. During retrieval, the Retrieval Agent can call `fetch_parent_chunk` to pull the full section when a child chunk alone does not provide enough context.

### Separation of embedding and generation models

Embeddings are produced by OpenAI (`text-embedding-3-small`) while all generation calls go to Anthropic Claude (`claude-sonnet-4-6`). The two are kept completely separate — the embedder has no dependency on the agent code and vice versa. Embeddings are used in three places: the knowledge base vector store, the memory similarity retrieval above the session threshold, and the context summary retrieval within the ingest pipeline. All three use the same embedder function so the embedding space is consistent.

### pgvectorscale DiskANN for vector search

The vector index uses pgvectorscale's DiskANN implementation rather than pgvector's HNSW. DiskANN is a streaming disk-based approximate nearest-neighbour algorithm that scales to large datasets without holding the full index in memory. The `docker-compose.yml` runs the `timescale/pgvectorscale-docker` image which includes both the `vector` and `vectorscale` PostgreSQL extensions. DiskANN indexes are created on the `documents.embedding` column and on the nullable `embedding` columns of all three memory tables, with a `WHERE embedding IS NOT NULL` predicate to exclude unembedded rows.

### Observability via Langfuse

All LLM calls are decorated with `@observe` from Langfuse. Each agent separates the observable generation call (`_call_claude`) from its public `run` function, giving a clean two-level trace: the agent span wraps the generation span. For the Retrieval Agent the entire agentic loop runs inside a single `_call_claude` invocation, so all iterations appear as one generation span — making it straightforward to see how many tool calls the agent made before terminating and what it retrieved.
