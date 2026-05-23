"""Tech stack agent: takes a project plan and retrieved technology docs, outputs MVP + full tech stack."""
import anthropic

from backend.config import get_settings
from backend.schemas.agents.tech_stack import TechStackAgentInput, TechStackAgentOutput

_SYSTEM_PROMPT = """\
You are a senior software architect. Given a project plan and relevant technology documentation, \
recommend the best tech stack for this project.

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

Base your recommendations on the project plan and the retrieved documentation. \
Avoid recommending technologies not relevant to the project's domain.\
"""


async def run(
    client: anthropic.AsyncAnthropic,
    input_: TechStackAgentInput,
) -> TechStackAgentOutput:
    settings = get_settings()

    plan = input_.project_plan
    docs_section = (
        "\n\n---\n\n".join(input_.retrieved_doc_contents)
        if input_.retrieved_doc_contents
        else "(no technology documentation retrieved)"
    )

    user_content = (
        f"Project plan:\n"
        f"Vision: {plan.vision}\n"
        f"Target audience: {plan.target_audience}\n"
        f"Problem: {plan.problem_addressed}\n"
        f"MVP scope: {plan.mvp_scope}\n\n"
        f"Retrieved technology documentation:\n{docs_section}"
    )

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
