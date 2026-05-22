import anthropic

from backend.config import get_settings
from backend.schemas.agents.clarifying import (
    ClarifyingAgentInput,
    ClarifyingAgentOutput,
    ProjectDefinitionAgentInput,
    ProjectDefinitionAgentOutput,
    ProjectSetupAgentInput,
    ProjectSetupAgentOutput,
)

# ---------------------------------------------------------------------------
# Prompt session: understand what the user thinks their prompt does
# ---------------------------------------------------------------------------

_SESSION_SYSTEM_PROMPT_TEMPLATE = """\
You are helping a developer understand and improve an AI system prompt.

Given the prompt they have written, ask 3-5 targeted questions that surface what they \
believe the prompt is instructing the AI to do. Focus on:
- What task or goal the prompt is meant to accomplish
- What the expected output looks like
- Any implicit assumptions the user has baked in
- What the prompt should NOT do (scope boundaries)

Do NOT ask about implementation details or tech stack. Ask about intent and expected behaviour.

{project_context}

IMPORTANT: Do not repeat any question already asked in a previous session for this project.
Previously asked questions (skip these entirely):
{previous_questions}\
"""


async def _call_session_questions(
    client: anthropic.AsyncAnthropic,
    input_: ClarifyingAgentInput,
) -> ClarifyingAgentOutput:
    settings = get_settings()

    project_context = (
        f"Project context: {input_.project_definition}"
        if input_.project_definition
        else ""
    )
    previous_questions_text = (
        "\n".join(f"- {q}" for q in input_.previous_questions)
        if input_.previous_questions
        else "(none)"
    )

    system_prompt = _SESSION_SYSTEM_PROMPT_TEMPLATE.format(
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
                "description": "Output the clarifying questions.",
                "input_schema": ClarifyingAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_questions"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ClarifyingAgentOutput.model_validate(tool_block.input)


async def run(
    client: anthropic.AsyncAnthropic, input_: ClarifyingAgentInput
) -> ClarifyingAgentOutput:
    return await _call_session_questions(client, input_)


# ---------------------------------------------------------------------------
# Project setup: refine a rough idea into clarifying questions
# ---------------------------------------------------------------------------

_SETUP_QUESTIONS_SYSTEM_PROMPT = """\
You are helping a developer define a software project they want to build with AI.

They have given you a rough idea of what they want to build. Ask 3-5 targeted questions \
that will clarify:
- What the system concretely does (inputs, outputs, who uses it)
- What role the AI component plays specifically
- The scope boundaries — what it does NOT do
- Any quality or constraint requirements

Be concise. Ask about what matters for defining the project, not how it will be built.\
"""


async def _call_setup_questions(
    client: anthropic.AsyncAnthropic,
    input_: ProjectSetupAgentInput,
) -> ProjectSetupAgentOutput:
    settings = get_settings()

    user_content = f"Project name: {input_.project_name}\n\nRough idea: {input_.rough_idea}"

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=_SETUP_QUESTIONS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_questions",
                "description": "Output the clarifying questions for project setup.",
                "input_schema": ProjectSetupAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_questions"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ProjectSetupAgentOutput.model_validate(tool_block.input)


async def run_project_setup_questions(
    client: anthropic.AsyncAnthropic, input_: ProjectSetupAgentInput
) -> ProjectSetupAgentOutput:
    return await _call_setup_questions(client, input_)


# ---------------------------------------------------------------------------
# Project setup: synthesize Q&A into a concrete project definition
# ---------------------------------------------------------------------------

_DEFINITION_SYSTEM_PROMPT = """\
You are helping a developer write a concrete definition for their project.

You have their rough idea and their answers to setup questions. Synthesise these into a \
2-3 sentence project definition that will serve as standing context for future AI prompt \
analysis sessions.

Requirements:
- Be specific and technical — name what the AI does, what it takes as input, what it produces
- Include any key constraints or quality requirements mentioned
- Do not include filler phrases or implementation detail
- Write in present tense as a factual description of the system\
"""


async def _call_project_definition(
    client: anthropic.AsyncAnthropic,
    input_: ProjectDefinitionAgentInput,
) -> ProjectDefinitionAgentOutput:
    settings = get_settings()

    qa_text = "\n".join(
        f"Q: {pair.question_text}\nA: {pair.answer_text}"
        for pair in input_.qa_pairs
    )
    user_content = (
        f"Project name: {input_.project_name}\n"
        f"Rough idea: {input_.rough_idea}\n\n"
        f"Setup Q&A:\n{qa_text}"
    )

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        system=_DEFINITION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_definition",
                "description": "Output the synthesised project definition.",
                "input_schema": ProjectDefinitionAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_definition"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ProjectDefinitionAgentOutput.model_validate(tool_block.input)


async def run_project_definition(
    client: anthropic.AsyncAnthropic, input_: ProjectDefinitionAgentInput
) -> ProjectDefinitionAgentOutput:
    return await _call_project_definition(client, input_)
