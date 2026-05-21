import anthropic
from langfuse import observe

from backend.config import get_settings
from backend.schemas.agents.clarifying import ClarifyingAgentInput, ClarifyingAgentOutput

_SYSTEM_PROMPT_TEMPLATE = """\
You are a senior AI engineer helping to improve prompts for RAG and agentic systems.

Given a prompt, generate 3-5 targeted clarifying questions that surface the user's true intent.
Focus on: retrieval scope, expected output format, level of technical depth, and context constraints.
Do NOT ask about tech stack, implementation details, or domain-specific knowledge.
Ask about goals, not methods.

{project_context}

IMPORTANT: Do not repeat any question that has already been asked in a previous session.
Previously asked questions (skip these — do not rephrase or ask a variant of them):
{previous_questions}\
"""


@observe(name="clarifying-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: ClarifyingAgentInput,
) -> ClarifyingAgentOutput:
    settings = get_settings()

    project_context = (
        f"Project context: {input_.project_summary}"
        if input_.project_summary
        else ""
    )
    previous_questions_text = (
        "\n".join(f"- {q}" for q in input_.previous_questions)
        if input_.previous_questions
        else "(none — this is the first session)"
    )

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        project_context=project_context,
        previous_questions=previous_questions_text,
    )

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": input_.original_prompt}],
        tools=[
            {
                "name": "output_questions",
                "description": "Output the clarifying questions as structured data.",
                "input_schema": ClarifyingAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_questions"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ClarifyingAgentOutput.model_validate(tool_block.input)


@observe(name="clarifying-agent")
async def run(
    client: anthropic.AsyncAnthropic, input_: ClarifyingAgentInput
) -> ClarifyingAgentOutput:
    return await _call_claude(client, input_)
