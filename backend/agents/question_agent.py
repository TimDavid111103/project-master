import anthropic
from langfuse import observe

from backend.config import get_settings
from backend.schemas.agents.question import QuestionAgentInput, QuestionAgentOutput

SYSTEM_PROMPT = """\
You are a senior AI engineer helping to improve prompts for RAG and agentic systems.

Given a prompt, generate 3-5 targeted clarifying questions that surface the user's true intent.
Focus on: retrieval scope, expected output format, level of technical depth, and context constraints.
Do NOT ask about tech stack, implementation details, or domain-specific knowledge.
Ask about goals, not methods.\
"""


@observe(name="question-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: QuestionAgentInput,
) -> QuestionAgentOutput:
    settings = get_settings()
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": input_.original_prompt}],
        tools=[
            {
                "name": "output_questions",
                "description": "Output the clarifying questions as structured data.",
                "input_schema": QuestionAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_questions"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return QuestionAgentOutput.model_validate(tool_block.input)


@observe(name="question-agent")
async def run(client: anthropic.AsyncAnthropic, input_: QuestionAgentInput) -> QuestionAgentOutput:
    return await _call_claude(client, input_)
