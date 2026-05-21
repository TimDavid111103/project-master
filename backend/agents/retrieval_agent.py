"""Agentic retrieval agent with a multi-tool loop over the vector DB.

The agent runs a loop, calling retrieval tools until it calls output_retrieved_docs.
All tool inputs from Claude are validated through Pydantic models before execution.
All tool results are fed back in the same conversation so Claude can reason across iterations.
"""
import json

import anthropic
from langfuse import observe
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

MAX_ITERATIONS = 8

_SYSTEM_PROMPT_TEMPLATE = """\
You are a retrieval agent for a RAG system that analyzes AI engineering prompts.

Your job is to retrieve the most relevant document chunks for the given user prompt and clarifications.

Steps:
1. Decide on a category and concept_tags from the taxonomy below that best describe the prompt.
2. Call metadata_filtered_search with those metadata values and a dense natural-language query.
3. If results are insufficient (fewer than {top_k} docs or low relevance), try:
   - expand_query to generate variant queries, then search again
   - multi_query to merge results from several query strings
   - fetch_parent_chunk to retrieve broader section context for a chunk
4. Use check_relevance to log your assessment of a document's relevance.
5. When you have gathered sufficient results, call output_retrieved_docs with the final list.

{project_context}

Taxonomy (use ONLY these values for category and concept_tags):
{taxonomy}\
"""

# ---------------------------------------------------------------------------
# Pydantic models for tool inputs — validated before execution in _dispatch_tool
# ---------------------------------------------------------------------------


class _MetadataFilteredSearchInput(BaseModel):
    query_text: str
    category: str
    concept_tags: list[str]
    top_k: int = 5


class _FetchParentChunkInput(BaseModel):
    child_doc_id: str


class _MultiQueryInput(BaseModel):
    queries: list[str]
    category: str
    concept_tags: list[str]


class _ExpandQueryInput(BaseModel):
    original_query_text: str


class _CheckRelevanceInput(BaseModel):
    doc_id: str
    is_relevant: bool
    rationale: str


class _ExpandQueryOutput(BaseModel):
    expanded_queries: list[str]


# ---------------------------------------------------------------------------
# Tool definitions — input_schema generated from Pydantic models
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "metadata_filtered_search",
        "description": "Search the vector DB filtered by category and concept_tags, then ranked by cosine similarity. Returns child-level chunks only.",
        "input_schema": _MetadataFilteredSearchInput.model_json_schema(),
    },
    {
        "name": "fetch_parent_chunk",
        "description": "Retrieve the parent section chunk of a given child chunk for broader context.",
        "input_schema": _FetchParentChunkInput.model_json_schema(),
    },
    {
        "name": "multi_query",
        "description": "Run metadata_filtered_search for each query string and return deduplicated merged results.",
        "input_schema": _MultiQueryInput.model_json_schema(),
    },
    {
        "name": "expand_query",
        "description": "Generate 2-3 semantically variant query strings to broaden a narrow query.",
        "input_schema": _ExpandQueryInput.model_json_schema(),
    },
    {
        "name": "check_relevance",
        "description": "Log a relevance assessment for a retrieved document. Does not affect retrieval — used for your own reasoning.",
        "input_schema": _CheckRelevanceInput.model_json_schema(),
    },
    {
        "name": "output_retrieved_docs",
        "description": "Return the final list of retrieved documents. Call this when you have gathered sufficient results.",
        "input_schema": RetrievalAgentOutput.model_json_schema(),
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _validate_taxonomy(
    category: str, concept_tags: list[str], taxonomy: dict
) -> tuple[str, list[str], list[str]]:
    """Validate and normalise category and concept_tags against taxonomy.

    Returns (category, valid_tags, warning_messages). Unknown tags are dropped
    and reported so Claude can self-correct on the next iteration.
    """
    warnings: list[str] = []
    valid_categories = list(taxonomy.keys())

    if category not in valid_categories:
        warnings.append(f"Unknown category '{category}'. Valid values: {valid_categories}. Defaulting to first.")
        category = valid_categories[0] if valid_categories else category

    all_tags = {tag for tags in taxonomy.values() for tag in tags}
    valid_tags = []
    for tag in concept_tags:
        if tag in all_tags:
            valid_tags.append(tag)
        else:
            warnings.append(f"Unknown concept_tag '{tag}' dropped.")

    return category, valid_tags, warnings


async def _metadata_filtered_search(
    inp: _MetadataFilteredSearchInput,
    db: AsyncSession,
    settings: Settings,
    taxonomy: dict,
) -> dict:
    category, concept_tags, warnings = _validate_taxonomy(
        inp.category, inp.concept_tags, taxonomy
    )
    query_embedding = await embed_text(inp.query_text, settings)

    stmt = (
        select(
            Document,
            Document.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(Document.chunk_level == "chunk")
        .where(Document.category == category)
        .where(Document.concept_tags.contains(concept_tags))
        .order_by("distance")
        .limit(inp.top_k)
    )
    rows = (await db.execute(stmt)).all()
    results = [
        RetrievedDocResult(
            doc_id=str(row.Document.id),
            content=row.Document.content,
            similarity_score=round(1.0 - row.distance, 4),
            chunk_level=row.Document.chunk_level,
            parent_id=str(row.Document.parent_id) if row.Document.parent_id else None,
        ).model_dump()
        for row in rows
    ]
    return {"results": results, "warnings": warnings} if warnings else {"results": results}


async def _fetch_parent_chunk(inp: _FetchParentChunkInput, db: AsyncSession) -> dict:
    child_stmt = select(Document).where(Document.id == inp.child_doc_id)
    child = (await db.execute(child_stmt)).scalar_one_or_none()
    if child is None:
        return {"error": f"Chunk {inp.child_doc_id} not found."}
    if child.parent_id is None:
        return {"error": f"Chunk {inp.child_doc_id} has no parent (it is already a section chunk)."}

    parent_stmt = select(Document).where(Document.id == child.parent_id)
    parent = (await db.execute(parent_stmt)).scalar_one_or_none()
    if parent is None:
        return {"error": f"Parent chunk for {inp.child_doc_id} not found."}

    return RetrievedDocResult(
        doc_id=str(parent.id),
        content=parent.content,
        similarity_score=0.0,
        chunk_level=parent.chunk_level,
        parent_id=None,
    ).model_dump()


async def _multi_query(
    inp: _MultiQueryInput,
    db: AsyncSession,
    settings: Settings,
    taxonomy: dict,
) -> dict:
    seen: set[str] = set()
    merged: list[dict] = []
    for query_text in inp.queries:
        result = await _metadata_filtered_search(
            _MetadataFilteredSearchInput(
                query_text=query_text,
                category=inp.category,
                concept_tags=inp.concept_tags,
                top_k=settings.rag_top_k,
            ),
            db,
            settings,
            taxonomy,
        )
        for doc in result.get("results", []):
            if doc["doc_id"] not in seen:
                seen.add(doc["doc_id"])
                merged.append(doc)
    merged.sort(key=lambda d: d["similarity_score"], reverse=True)
    return {"results": merged}


async def _expand_query(
    inp: _ExpandQueryInput,
    client: anthropic.AsyncAnthropic,
    settings: Settings,
) -> dict:
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=256,
        system="Generate 2-3 semantically variant phrasings of the given query to broaden search coverage.",
        messages=[{"role": "user", "content": inp.original_query_text}],
        tools=[
            {
                "name": "output_expansions",
                "description": "Output the expanded query variants.",
                "input_schema": _ExpandQueryOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_expansions"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return _ExpandQueryOutput.model_validate(tool_block.input).model_dump()


# ---------------------------------------------------------------------------
# Tool dispatcher — validates every tool input through the corresponding model
# ---------------------------------------------------------------------------


async def _dispatch_tool(
    tool_use_block,
    db: AsyncSession,
    client: anthropic.AsyncAnthropic,
    settings: Settings,
    taxonomy: dict,
) -> dict:
    name = tool_use_block.name
    args = tool_use_block.input

    if name == "metadata_filtered_search":
        return await _metadata_filtered_search(
            _MetadataFilteredSearchInput.model_validate(args), db, settings, taxonomy
        )
    elif name == "fetch_parent_chunk":
        return await _fetch_parent_chunk(_FetchParentChunkInput.model_validate(args), db)
    elif name == "multi_query":
        return await _multi_query(
            _MultiQueryInput.model_validate(args), db, settings, taxonomy
        )
    elif name == "expand_query":
        return await _expand_query(
            _ExpandQueryInput.model_validate(args), client, settings
        )
    elif name == "check_relevance":
        _CheckRelevanceInput.model_validate(args)  # validate even though result is unused
        return {"acknowledged": True}
    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@observe(name="retrieval-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: RetrievalAgentInput,
    db: AsyncSession,
    settings: Settings,
) -> RetrievalAgentOutput:
    project_context = (
        f"Project context: {input_.project_summary}" if input_.project_summary else ""
    )
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        top_k=settings.rag_top_k,
        project_context=project_context,
        taxonomy=json.dumps(input_.taxonomy, indent=2),
    )
    qa_text = "\n".join(
        f"Q: {pair.question_text}\nA: {pair.answer_text}" for pair in input_.qa_pairs
    )
    user_content = (
        f"Prompt to analyze:\n{input_.original_prompt}\n\n"
        f"Clarifications from the user:\n{qa_text}"
    )

    messages: list[dict] = [{"role": "user", "content": user_content}]

    for _ in range(MAX_ITERATIONS):
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            tools=_TOOLS,
            tool_choice={"type": "auto"},
        )
        # Append the raw content list so tool_use blocks round-trip correctly
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        terminal = next((b for b in tool_uses if b.name == "output_retrieved_docs"), None)
        if terminal:
            return RetrievalAgentOutput.model_validate(terminal.input)

        if response.stop_reason == "end_turn" and not tool_uses:
            raise RuntimeError("Retrieval agent ended without calling output_retrieved_docs")

        tool_results = []
        for tu in tool_uses:
            result = await _dispatch_tool(tu, db, client, settings, input_.taxonomy)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(
        f"Retrieval agent exceeded {MAX_ITERATIONS} iterations without terminating"
    )


@observe(name="retrieval-agent")
async def run(
    client: anthropic.AsyncAnthropic,
    input_: RetrievalAgentInput,
    db: AsyncSession,
    settings: Settings,
) -> RetrievalAgentOutput:
    return await _call_claude(client, input_, db, settings)
