# Project Master

A tool for developers and founders turning raw ideas into structured project plans. You describe your idea in a short form, then have a short conversational chat with an AI that builds out your vision, target audience, problem statement, and MVP scope. Once the plan is confirmed, the system generates two tech stacks — one optimised for an MVP, one for a full production system.

The system is not a general-purpose chatbot. It is a focused two-stage pipeline — ideate, then analyse — designed specifically around translating rough ideas into actionable project and technology plans.

---

## File Structure

```
project-master/
│
├── backend/
│   ├── agents/
│   │   ├── base.py                   # Anthropic client factory and shared agent setup
│   │   ├── ideation_agent.py         # Stage 1 — conversational ideation chat (vision, audience, problem, MVP scope)
│   │   └── tech_stack_agent.py       # Stage 2 — generates MVP and full-product tech stacks from the project plan
│   │
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy model: Project
│   │   └── engine.py                 # Async database engine and session factory
│   │
│   ├── schemas/
│   │   ├── agents/
│   │   │   ├── ideation.py           # ChatMessage, ProjectPlan, IdeationChatOutput
│   │   │   └── tech_stack.py         # TechStackItem, TechStack, TechStackAgentInput/Output
│   │   └── api/
│   │       ├── pipeline.py           # Request and response types for pipeline endpoints
│   │       └── projects.py           # Request and response types for the projects endpoint
│   │
│   ├── services/
│   │   └── pipeline_service.py       # Orchestrates tech stack generation → DB persistence
│   │
│   ├── api/v1/
│   │   ├── router.py                 # v1 API router
│   │   └── endpoints/
│   │       ├── pipeline.py           # /pipeline/chat and /pipeline/analyze endpoints
│   │       └── projects.py           # /projects CRUD endpoints
│   │
│   ├── config.py                     # All settings loaded from environment variables
│   ├── dependencies.py               # FastAPI dependency injection (database session, settings)
│   └── main.py                       # FastAPI app factory, CORS middleware, lifespan
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                # Root layout and global styles
│   │   └── page.tsx                  # Entry point — manages view state across all screens
│   ├── components/
│   │   ├── HomeView.tsx              # Project list: Draft / Complete badges, navigation
│   │   ├── NewProjectFlow.tsx        # Project creation form (name + rough idea)
│   │   ├── IdeationChatFlow.tsx      # Conversational ideation UI + analysis loading state
│   │   ├── ProjectDetailView.tsx     # Project plan cards + MVP and full-product tech stacks
│   │   ├── AsteriskLogo.tsx          # Shared logo component
│   │   └── ui/                       # shadcn/ui primitives
│   ├── hooks/
│   │   ├── useIdeationChat.ts        # State and logic for the ideation chat + pipeline trigger
│   │   └── useProjects.ts            # Fetches and manages the project list
│   └── lib/
│       ├── api.ts                    # All backend API calls
│       ├── types.ts                  # Shared TypeScript types mirroring backend schemas
│       └── utils.ts                  # Utility helpers
│
├── alembic/versions/
│   ├── 0001_initial.py               # Initial schema
│   ├── 0002_v2_schema.py             # Project memory tables
│   ├── 0003_v3_schema.py             # Projects table with rough_idea and definition columns
│   ├── 0004_v4_schema.py             # Adds project_plan_json and tech_stack_json
│   └── 0005_v5_simplify_documents.py # Simplifies document columns
│
├── docker-compose.yml                # Runs the PostgreSQL database
├── Dockerfile                        # Backend container definition
├── main.py                           # Root entry point for running the backend server
└── pyproject.toml                    # Python project config and dependencies
```

---

## Backend

The backend is a FastAPI application built around a two-stage pipeline. Stage one is a stateless conversational agent that builds a structured `ProjectPlan` from a freeform idea over 2–6 turns. Stage two runs when the plan is confirmed: a tech stack agent takes the plan and produces two tech stacks using its built-in knowledge of the technology landscape.

All agents use Claude's tool use API with `tool_choice` set to force a specific tool on every call, guaranteeing that every LLM response is a validated Pydantic model — there is no free-text parsing anywhere in the pipeline.

The pipeline service is the single place where tech stack generation and DB persistence are wired together.

## Frontend

The frontend is a Next.js application. View state is managed in a single top-level component (`page.tsx`) as a discriminated union so transitions between screens are explicit and type-safe. Each screen delegates its data-fetching and state management to a dedicated hook, keeping the components themselves presentational. All backend communication goes through a single API module.

## Agents

**Ideation agent** — conversational. Receives a `conversation_history` list on every turn (stateless). Builds out vision, target audience, problem addressed, and MVP scope by asking 1–2 focused questions at a time. Sets `is_complete: true` and emits a structured `ProjectPlan` once it has enough information (minimum 2 turns, maximum 5–6).

**Tech stack agent** — single call. Receives the `ProjectPlan` and returns two `TechStack` lists: one for an MVP (4–7 managed services, minimal ops overhead) and one for a full production system (8–12 items, independently scalable). Recommendations are based on the project plan and the model's knowledge of the technology landscape.

## Schemas

All data contracts are defined as Pydantic models before any logic is written. Agent inputs and outputs, API request and response bodies all have explicit types. The agent schemas serve a dual purpose: they define the tool input schemas that Claude receives, and they validate tool call arguments before any business logic runs.
