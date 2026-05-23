"""Conversational ideation agent that gathers project definition through back-and-forth chat.

Tracks four checklist items internally (vision, target audience, problem, MVP scope)
and decides when the conversation has enough information to produce a structured plan.
"""
import anthropic

from backend.config import get_settings
from backend.schemas.agents.ideation import (
    ChatMessage,
    IdeationChatOutput,
    ProjectPlan,
)

_SYSTEM_PROMPT = """\
You are a project planning assistant. Your job is to have a focused, natural conversation \
with the user to understand their project idea well enough to create a solid project plan.

You are collecting four specific pieces of information:
1. Vision — what the project ultimately is and does
2. Target audience — who it is built for and what matters most to them
3. Problem being addressed — the specific pain point or gap this fills
4. Practical MVP scope — the simplest version of the product that delivers real value

How to behave:
- Ask natural, open questions — one or two at a time, never a list
- Reference and build on what the user has already told you
- When you have a clear sense of the vision, briefly confirm it: \
  "So if I'm understanding right, [one-sentence summary of vision] — is that right?"
- Keep the conversation efficient; 2–3 turns is ideal
- Count the assistant turns already in the conversation history. \
  After 5 assistant turns, you MUST set is_complete to true regardless.

When you have gathered all four items to a reasonable degree of completeness — or after \
5 assistant turns — call the output_result tool and set is_complete to true. \
The project_plan field must be populated whenever is_complete is true.

When is_complete is false, set project_plan to null and write your next question \
or confirmation in agent_message.\
"""


async def run(
    client: anthropic.AsyncAnthropic,
    user_message: str,
    conversation_history: list[ChatMessage],
) -> IdeationChatOutput:
    settings = get_settings()

    messages: list[dict] = [
        {"role": m.role, "content": m.content}
        for m in conversation_history
    ]
    messages.append({"role": "user", "content": user_message})

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=messages,
        tools=[
            {
                "name": "output_result",
                "description": "Output the ideation result for this turn.",
                "input_schema": IdeationChatOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_result"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    output = IdeationChatOutput.model_validate(tool_block.input)

    if output.is_complete and output.project_plan is None:
        raise ValueError("Agent set is_complete=true but did not provide project_plan")

    return output
