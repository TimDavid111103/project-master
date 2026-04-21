import json

import anthropic
from langfuse import observe

from backend.config import get_settings
from backend.schemas.agents.reformulation import (
    ReformulationAgentInput,
    ReformulationAgentOutput,
)

_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert at transforming user prompts and clarifying answers into optimized vector search queries.

You must output a structured query containing:
- category: one of the top-level keys from the taxonomy below
- concept_tags: a list of leaf values from the taxonomy below (choose the most relevant)
- query_text: a clear, dense natural-language query suitable for semantic similarity search

Taxonomy (your output must use only these values):
{taxonomy}

Do not invent categories or tags outside of the taxonomy.\
"""


@observe(name="reformulation-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: ReformulationAgentInput,
) -> ReformulationAgentOutput:
    settings = get_settings()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        taxonomy=json.dumps(input_.taxonomy, indent=2)
    )
    user_content = (
        f"Original prompt:\n{input_.original_prompt}\n\n"
        f"Clarifying questions and answers:\n"
        + "\n".join(
            f"Q: {q.question_text}\nA: {a.answer_text}"
            for q, a in zip(input_.questions, input_.answers)
        )
    )
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_query",
                "description": "Output the reformulated query as structured data.",
                "input_schema": ReformulationAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_query"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ReformulationAgentOutput.model_validate(tool_block.input)


@observe(name="reformulation-agent")
async def run(
    client: anthropic.AsyncAnthropic, input_: ReformulationAgentInput
) -> ReformulationAgentOutput:
    return await _call_claude(client, input_)
