import anthropic

from backend.config import get_settings
from backend.schemas.agents.analysis import (
    IntentTranslationAgentInput,
    IntentTranslationAgentOutput,
)

SYSTEM_PROMPT = """\
You are an AI behaviour analyst. Your job is to read an AI system prompt and describe \
plainly what it is actually instructing the AI to do — not what the author intended, \
but what the text literally instructs.

You have access to:
1. The prompt itself
2. Q&A where the user describes what they believe the prompt does
3. Past translations for this project (for continuity)

Produce an IntentTranslation with three fields:

what_the_prompt_instructs
  One or two sentences. State precisely what behaviour the prompt produces in an AI model. \
  Be literal. If the prompt is ambiguous, describe the most likely interpretation.

assumptions_made
  A list of implicit assumptions baked into the prompt that are not stated explicitly. \
  These are things the prompt takes for granted — about the user, the context, the model, \
  the output format, etc.

potential_gaps
  A list of things the user likely wanted (based on the Q&A) that the prompt does not \
  address or under-specifies. Be concrete — name what is missing and why it matters.\
"""


async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: IntentTranslationAgentInput,
) -> IntentTranslationAgentOutput:
    settings = get_settings()

    qa_text = "\n".join(
        f"Q: {pair.question_text}\nA: {pair.answer_text}" for pair in input_.qa_pairs
    )
    past_context = (
        "\n\n".join(
            f"[Past translation {i + 1}]\n{t}"
            for i, t in enumerate(input_.past_translations)
        )
        if input_.past_translations
        else "(no prior translations for this project)"
    )
    project_context = (
        f"Project context: {input_.project_definition}\n\n"
        if input_.project_definition
        else ""
    )

    user_content = (
        f"{project_context}"
        f"Prompt to translate:\n{input_.original_prompt}\n\n"
        f"User's description of what the prompt does (Q&A):\n{qa_text}\n\n"
        f"Past translations for this project:\n{past_context}"
    )

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_translation",
                "description": "Output the intent translation.",
                "input_schema": IntentTranslationAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_translation"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return IntentTranslationAgentOutput.model_validate(tool_block.input)


async def run(
    client: anthropic.AsyncAnthropic, input_: IntentTranslationAgentInput
) -> IntentTranslationAgentOutput:
    return await _call_claude(client, input_)
