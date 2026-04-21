import anthropic
from langfuse import observe

from backend.config import get_settings
from backend.schemas.agents.synthesizer import SynthesizerAgentInput, SynthesizerAgentOutput

SYSTEM_PROMPT = """\
You are an expert prompt engineer. Given an original prompt, the user's clarifications, and relevant reference knowledge, you must:

1. Rewrite the prompt to be clearer, more specific, and more effective for its intended purpose.
2. Provide a plain-language analysis explaining what changed and why, without referencing any domain-specific knowledge.

The revised prompt should preserve the user's intent while improving structure, specificity, and retrievability.
The analysis should be accessible to any software engineer, not just domain experts.\
"""


@observe(name="synthesizer-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: SynthesizerAgentInput,
) -> SynthesizerAgentOutput:
    settings = get_settings()
    rag_context = "\n\n---\n\n".join(
        f"[Document {i + 1}]\n{doc.content}"
        for i, doc in enumerate(input_.retrieved_documents)
    )
    qa_pairs = "\n".join(
        f"Q: {a.question_id} — A: {a.answer_text}" for a in input_.answers
    )
    user_content = (
        f"Original prompt:\n{input_.original_prompt}\n\n"
        f"User clarifications:\n{qa_pairs}\n\n"
        f"Reference knowledge:\n{rag_context}"
    )
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_result",
                "description": "Output the revised prompt and analysis as structured data.",
                "input_schema": SynthesizerAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_result"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return SynthesizerAgentOutput.model_validate(tool_block.input)


@observe(name="synthesizer-agent")
async def run(
    client: anthropic.AsyncAnthropic, input_: SynthesizerAgentInput
) -> SynthesizerAgentOutput:
    return await _call_claude(client, input_)
