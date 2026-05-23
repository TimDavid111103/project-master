"""Agentic retrieval agent with three tools: vector_search, expand_query, multi_query.

Runs a loop until the agent calls output_retrieved_docs with its final selection.
"""
import json

import anthropic
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.db.models import Document
from backend.rag.embedder import embed_text
from backend.schemas.agents.retrieval import (
    RetrievalAgentInput,
    RetrievalAgentOutput,
    RetrievedDocResult,
)

MAX_ITERATIONS = 5

_SYSTEM_PROMPT = """\
You are a retrieval agent for a technology knowledge base. Given a project plan, your job is \
to find the most relevant documents about technologies and tools that would help recommend \
a good tech stack for this project.

You have three tools:
- vector_search: search the database with a natural-language query
- expand_query: generate 2–3 variant phrasings of a query to broaden coverage
- multi_query: run vector_search for several queries at once and get deduplicated results

Strategy:
1. Start with a direct vector_search using a query derived from the project plan
2. If results feel narrow or miss important categories, use expand_query or multi_query
3. Use check_relevance to log your reasoning about specific documents
4. When you have enough relevant results (aim for 5–10), call output_retrieved_docs

Project plan:
Vision: {vision}
Target audience: {target_audience}
Problem: {problem_addressed}
MVP scope: {mvp_scope}\
"""


# ---------------------------------------------------------------------------
# Tool input models
# ---------------------------------------------------------------------------


class _VectorSearchInput(BaseModel):
    query_text: str
    top_k: int = 8


class _ExpandQueryInput(BaseModel):
    original_query: str


class _MultiQueryInput(BaseModel):
    queries: list[str]
    top_k_per_query: int = 5


class _CheckRelevanceInput(BaseModel):
    doc_id: str
    is_relevant: bool
    rationale: str


class _ExpandQueryOutput(BaseModel):
    queries: list[str]


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "vector_search",
        "description": "Search the technology knowledge base with a natural-language query. Returns the most similar documents by cosine similarity.",
        "input_schema": _VectorSearchInput.model_json_schema(),
    },
    {
        "name": "expand_query",
        "description": "Generate 2–3 semantically variant phrasings of a query to broaden coverage.",
        "input_schema": _ExpandQueryInput.model_json_schema(),
    },
    {
        "name": "multi_query",
        "description": "Run vector_search for each query and return deduplicated merged results.",
        "input_schema": _MultiQueryInput.model_json_schema(),
    },
    {
        "name": "check_relevance",
        "description": "Log your assessment of a document's relevance. Does not affect retrieval — used for your own reasoning.",
        "input_schema": _CheckRelevanceInput.model_json_schema(),
    },
    {
        "name": "output_retrieved_docs",
        "description": "Return the final list of relevant documents. Call this when you have gathered sufficient results.",
        "input_schema": RetrievalAgentOutput.model_json_schema(),
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _vector_search(
    inp: _VectorSearchInput,
    db: AsyncSession,
    settings: Settings,
) -> dict:
    embedding = await embed_text(inp.query_text, settings)
    stmt = (
        select(
            Document,
            Document.embedding.cosine_distance(embedding).label("distance"),
        )
        .order_by("distance")
        .limit(inp.top_k)
    )
    rows = (await db.execute(stmt)).all()
    results = [
        RetrievedDocResult(
            doc_id=str(row.Document.id),
            content=row.Document.content,
            similarity_score=round(1.0 - row.distance, 4),
        ).model_dump()
        for row in rows
    ]
    return {"results": results}


async def _expand_query(
    inp: _ExpandQueryInput,
    client: anthropic.AsyncAnthropic,
    settings: Settings,
) -> dict:
    response = await client.messages.create(
        model=settings.claude_retrieval_model,
        max_tokens=256,
        system="Generate 2–3 semantically variant phrasings of the given search query to broaden coverage.",
        messages=[{"role": "user", "content": inp.original_query}],
        tools=[
            {
                "name": "output_queries",
                "description": "Output the variant queries.",
                "input_schema": _ExpandQueryOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_queries"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return _ExpandQueryOutput.model_validate(tool_block.input).model_dump()


async def _multi_query(
    inp: _MultiQueryInput,
    db: AsyncSession,
    settings: Settings,
) -> dict:
    seen: set[str] = set()
    merged: list[dict] = []
    for query_text in inp.queries:
        result = await _vector_search(
            _VectorSearchInput(query_text=query_text, top_k=inp.top_k_per_query),
            db,
            settings,
        )
        for doc in result.get("results", []):
            if doc["doc_id"] not in seen:
                seen.add(doc["doc_id"])
                merged.append(doc)
    merged.sort(key=lambda d: d["similarity_score"], reverse=True)
    return {"results": merged}


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


async def _dispatch_tool(
    tool_use_block,
    db: AsyncSession,
    client: anthropic.AsyncAnthropic,
    settings: Settings,
) -> dict:
    name = tool_use_block.name
    args = tool_use_block.input

    if name == "vector_search":
        return await _vector_search(_VectorSearchInput.model_validate(args), db, settings)
    elif name == "expand_query":
        return await _expand_query(_ExpandQueryInput.model_validate(args), client, settings)
    elif name == "multi_query":
        return await _multi_query(_MultiQueryInput.model_validate(args), db, settings)
    elif name == "check_relevance":
        _CheckRelevanceInput.model_validate(args)
        return {"acknowledged": True}
    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------


async def run(
    client: anthropic.AsyncAnthropic,
    input_: RetrievalAgentInput,
    db: AsyncSession,
    settings: Settings,
) -> RetrievalAgentOutput:
    plan = input_.project_plan
    system_prompt = _SYSTEM_PROMPT.format(
        vision=plan.vision,
        target_audience=plan.target_audience,
        problem_addressed=plan.problem_addressed,
        mvp_scope=plan.mvp_scope,
    )

    messages: list[dict] = [
        {
            "role": "user",
            "content": "Please find the most relevant technology documentation for this project.",
        }
    ]

    for iteration in range(MAX_ITERATIONS):
        is_last = iteration == MAX_ITERATIONS - 1
        response = await client.messages.create(
            model=settings.claude_retrieval_model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=_TOOLS,
            tool_choice=(
                {"type": "tool", "name": "output_retrieved_docs"}
                if is_last
                else {"type": "auto"}
            ),
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        terminal = next((b for b in tool_uses if b.name == "output_retrieved_docs"), None)
        if terminal:
            return RetrievalAgentOutput.model_validate(terminal.input)

        if response.stop_reason == "end_turn" and not tool_uses:
            raise RuntimeError("Retrieval agent ended without calling output_retrieved_docs")

        tool_results = []
        for tu in tool_uses:
            result = await _dispatch_tool(tu, db, client, settings)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("Retrieval agent exceeded max iterations")
