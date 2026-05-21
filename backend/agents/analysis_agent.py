import anthropic
from langfuse import observe

from backend.config import get_settings
from backend.schemas.agents.analysis import AnalysisAgentInput, AnalysisAgentOutput

SYSTEM_PROMPT = """\
You are an expert prompt engineer evaluating an AI system prompt against three dimensions.

You have access to:
1. The original prompt written by the user
2. Clarifying Q&A that reveals the user's true intent
3. Retrieved technical reference knowledge
4. Past analyses for this project (for trend awareness)

Grade the prompt on each dimension using this scale:
  F = fundamentally broken or missing
  D = major issues that undermine the goal
  C = below standard, significant gaps
  B = solid but with notable weaknesses
  A = excellent, minor issues only
  S = outstanding — a model example

Dimensions:
- intent_accuracy: How well does the prompt reflect the user's actual intent as revealed by the Q&A?
  The Q&A answers are ground truth. Grade on how closely the prompt matches what the user said they wanted.

- technical_language: Is technical terminology used appropriately for the task's complexity?
  Too much jargon for a simple task is penalized. Too little for a complex task is also penalized.
  Incorrect use of technical terms is penalized most heavily.

- standards_alignment: Does the prompt follow professional standards for AI engineering?
  Would following this prompt produce production-quality results?
  Grade on how well it matches what an experienced engineer would write.

Rules:
- Explanations must be specific and reference the actual prompt content.
- Name technical concepts correctly. Do not use vague language.
- Explanations must be actionable — tell the user exactly what to change and why.
- Do not rewrite the prompt. Analysis only.\
"""


@observe(name="analysis-agent-llm-call", as_type="generation")
async def _call_claude(
    client: anthropic.AsyncAnthropic,
    input_: AnalysisAgentInput,
) -> AnalysisAgentOutput:
    settings = get_settings()

    rag_context = "\n\n---\n\n".join(
        f"[Reference {i + 1}]\n{doc.content}"
        for i, doc in enumerate(input_.retrieved_documents)
    )
    qa_text = "\n".join(
        f"Q: {pair.question_text}\nA: {pair.answer_text}" for pair in input_.qa_pairs
    )
    past_context = (
        "\n\n".join(f"[Past analysis {i + 1}]\n{a}" for i, a in enumerate(input_.past_analyses))
        if input_.past_analyses
        else "(no prior analyses for this project)"
    )
    project_context = (
        f"Project context: {input_.project_summary}\n\n"
        if input_.project_summary
        else ""
    )

    user_content = (
        f"{project_context}"
        f"Prompt to analyze:\n{input_.original_prompt}\n\n"
        f"User's clarifications (ground truth for intent):\n{qa_text}\n\n"
        f"Retrieved reference knowledge:\n{rag_context}\n\n"
        f"Past analyses for this project:\n{past_context}"
    )

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        tools=[
            {
                "name": "output_analysis",
                "description": "Output the structured prompt analysis with grades and explanations.",
                "input_schema": AnalysisAgentOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_analysis"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return AnalysisAgentOutput.model_validate(tool_block.input)


@observe(name="analysis-agent")
async def run(
    client: anthropic.AsyncAnthropic, input_: AnalysisAgentInput
) -> AnalysisAgentOutput:
    return await _call_claude(client, input_)
