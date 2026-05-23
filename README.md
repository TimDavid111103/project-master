# Prompt Master

A tool for engineers building AI systems. You create a project, paste a prompt, answer a few clarifying questions, and receive a plain-language translation of what your prompt actually instructs — not what you intended, but what the text literally tells the model to do. The system surfaces the assumptions baked into your prompt and the gaps between what you wrote and what you likely wanted. It gets smarter over time, reading your project history before generating questions and before producing a translation.

The system is not a general-purpose chatbot. It is a focused two-step pipeline — clarify, then translate — designed specifically around understanding and improving prompts for AI systems.

---

## File Structure

```
prompt-master/
│
├── backend/
│   ├── agents/
│   │   ├── base.py                   # Anthropic client factory and shared agent setup
│   │   ├── clarifying_agent.py       # Stage 1 — generates clarifying questions using project memory
│   │   └── analysis_agent.py         # Stage 2 — translates what the prompt literally instructs
│   │
│   ├── rag/
│   │   ├── chunker.py                # Hierarchical document chunker with Claude-generated context summaries
│   │   └── embedder.py               # OpenAI embeddings wrapper
│   │
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy models for all tables
│   │   └── engine.py                 # Async database engine and session factory
│   │
│   ├── schemas/
│   │   ├── agents/
│   │   │   ├── common.py             # Shared types used across agents
│   │   │   ├── clarifying.py         # Input and output types for the clarifying agent
│   │   │   ├── retrieval.py          # Shared QAPair type used across the pipeline
│   │   │   └── analysis.py           # Input and output types for the intent translation agent
│   │   ├── api/
│   │   │   ├── session.py            # Request and response types for session endpoints
│   │   │   └── projects.py           # Request and response types for the projects endpoint
│   │   └── memory.py                 # ProjectMemory — the context object passed into agents
│   │
│   ├── services/
│   │   ├── session_service.py        # Orchestrates the full pipeline — wires both agents and memory
│   │   └── memory_service.py         # Reads and writes per-project memory across sessions
│   │
│   ├── api/v1/
│   │   ├── router.py                 # v1 API router
│   │   └── endpoints/
│   │       ├── session.py            # /session/start and /session/respond endpoints
│   │       └── projects.py           # /projects endpoint
│   │
│   ├── config.py                     # All settings loaded from environment variables
│   ├── dependencies.py               # FastAPI dependency injection (database session, etc.)
│   └── main.py                       # FastAPI app factory, CORS middleware, lifespan
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                # Root layout and global styles
│   │   └── page.tsx                  # Entry page
│   ├── components/
│   │   ├── HomeView.tsx              # Project list and navigation
│   │   ├── NewProjectFlow.tsx        # Step-by-step project creation flow
│   │   ├── ProjectDetailView.tsx     # Project history and session browser
│   │   ├── PromptSessionFlow.tsx     # The main prompt analysis session UI
│   │   ├── AsteriskLogo.tsx          # Shared logo component
│   │   └── ui/                       # shadcn/ui primitives
│   ├── hooks/
│   │   ├── useProjectSetup.ts        # State and logic for creating a new project
│   │   ├── useProjects.ts            # Fetches and manages the project list
│   │   └── useSession.ts             # Manages a prompt analysis session end-to-end
│   └── lib/
│       ├── api.ts                    # All backend API calls
│       ├── types.ts                  # Shared TypeScript types mirroring backend schemas
│       └── utils.ts                  # Utility helpers
│
├── scripts/
│   ├── taxonomy_discovery.py         # Uses Claude to discover categories and tags from the raw corpus
│   ├── ingest.py                     # Chunks, embeds, and writes corpus documents into the database
│   └── test_pipeline.py              # Manual end-to-end pipeline smoke test
│
├── tests/
│   ├── conftest.py                   # Shared fixtures and test database setup
│   └── integration/
│       ├── test_session_start.py     # Integration tests for session start
│       └── test_session_respond.py   # Integration tests for session respond
│
├── alembic/versions/
│   ├── 0001_initial.py               # Initial schema — documents table with pgvector HNSW index
│   ├── 0002_v2_schema.py             # Adds project memory tables and hierarchical chunking columns
│   └── 0003_v3_schema.py             # v3 schema changes
│
├── corpus/                           # Legacy document corpus from a prior RAG retrieval stage
├── taxonomy.json                     # Legacy taxonomy from a prior RAG retrieval stage
├── docker-compose.yml                # Runs the pgvector database
├── Dockerfile                        # Backend container definition
├── main.py                           # Root entry point for running the backend server
└── pyproject.toml                    # Python project config and dependencies
```

---

## Backend

The backend is a FastAPI application built around a two-stage pipeline. Each stage is implemented as a discrete agent: the Clarifying Agent generates questions tailored to the current project, and the Analysis Agent translates what the prompt literally instructs. Both agents use Claude's tool use API to guarantee that every LLM response is a validated Pydantic model — there is no free-text parsing anywhere in the pipeline.

The session service is the single place where agents and memory are wired together. It is the only layer that knows about the full pipeline flow.

## Frontend

The frontend is a Next.js application. The view layer is split into a small set of focused components: a home view for navigating projects, a creation flow for setting up new projects, a detail view for browsing a project's history, and a session flow for running a prompt analysis. Each component delegates its data-fetching and state management to a dedicated hook, keeping the components themselves presentational. All backend communication goes through a single API module.

## Agents

Each agent is a self-contained unit with a single responsibility. The Clarifying Agent reads project memory before generating questions and suppresses any question already asked in a prior session. The Analysis Agent receives the prompt, the Q&A pairs, and project history, and returns a plain-language translation describing what the prompt literally instructs — along with the implicit assumptions it makes and the gaps between intent and content.

## Schemas

All data contracts are defined as Pydantic models before any logic is written. Agent inputs and outputs, API request and response bodies, and the internal memory context object all have explicit types. The agent schemas serve a dual purpose: they define the tool input schemas that Claude receives, and they validate tool call arguments before any business logic runs.

## Memory

Every project maintains its own isolated memory that persists prompts, Q&A pairs, and translations across sessions. Before each pipeline run, the memory service reads this history and assembles a context object that both agents can use. Past questions are always retrieved in full for deduplication. For projects with longer histories, the service switches to similarity-based retrieval, embedding the current prompt and fetching the most relevant past entries rather than passing everything at once.

## Scripts

The scripts directory contains offline tooling that runs outside the main application. A pipeline smoke test script exercises the full session flow end-to-end without going through the HTTP layer. The taxonomy discovery and ingest scripts are legacy tooling from a prior version of the project that included a RAG retrieval stage.
