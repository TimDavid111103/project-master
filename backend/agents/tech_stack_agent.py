"""Tech stack agent: takes a project plan and outputs MVP + full tech stack."""
import anthropic

from backend.config import get_settings
from backend.schemas.agents.tech_stack import TechStackAgentInput, TechStackAgentOutput

_SYSTEM_PROMPT = """\
You are a senior software architect. Given a project plan, recommend the best tech stack \
for this project.

Produce two stacks:

mvp — The minimal set of technologies to build the core product quickly and ship it. \
Favour managed services, low ops overhead, and fast iteration. Typically 4–7 items.

full_product — The recommended stack for a production-ready, scalable version of the same product. \
May introduce more robust infrastructure, observability, and specialised tools. Typically 8–12 items.

For each technology provide:
- name: the technology name (e.g. "Next.js", "PostgreSQL", "Stripe")
- category: one of: Frontend, Backend, Database, Authentication, Infrastructure, AI/ML, Mobile, \
  Payments, Storage, Monitoring
- rationale: 1–2 sentences explaining why it fits this specific project

Base your recommendations on the project plan and your knowledge of the technology landscape. \
Avoid recommending technologies not relevant to the project's domain.

EXISTING TECH STACK PRIORITY RULE:
When the user has provided their existing tech stack, you MUST treat it as a strong constraint. \
Include every applicable technology from their existing stack in BOTH the mvp and full_product stacks. \
Only omit an existing technology if it is fundamentally incompatible with this project type. \
When their existing technology covers a category, do not replace it with an alternative — use it. \
The rationale for included existing technologies should note that it is already in use by the team.\
"""


async def run(
    client: anthropic.AsyncAnthropic,
    input_: TechStackAgentInput,
) -> TechStackAgentOutput:
    settings = get_settings()

    plan = input_.project_plan
    user_content_parts = [
        f"Project plan:\n"
        f"Vision: {plan.vision}\n"
        f"Target audience: {plan.target_audience}\n"
        f"Problem: {plan.problem_addressed}\n"
        f"MVP scope: {plan.mvp_scope}",
    ]

    if input_.user_tech_stack:
        stack_list = ", ".join(input_.user_tech_stack)
        user_content_parts.append(
            f"\nUser's existing tech stack (MUST be prioritised and included wherever applicable):\n"
            f"{stack_list}"
        )

    user_content = "\n".join(user_content_parts)

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_tech_stack",
                "description": "Output the recommended tech stack.",
                "input_schema": TechStackAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_tech_stack"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return TechStackAgentOutput.model_validate(tool_block.input)
