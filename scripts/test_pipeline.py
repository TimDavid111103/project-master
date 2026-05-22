"""
Quick end-to-end test that bypasses project creation and Q&A steps.
Feeds a pre-prepared prompt + answers directly into the retrieval agent,
then passes the output to the intent translation agent and prints the result.

Usage (from project root):  python -m scripts.test_pipeline
Usage (from anywhere):      uv run scripts/test_pipeline.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow running as a standalone script from any directory
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import os; os.chdir(PROJECT_ROOT)

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import retrieval_agent, analysis_agent
from backend.config import get_settings
from backend.db.engine import dispose_engine, _get_engine
from backend.schemas.agents.retrieval import QAPair, RetrievalAgentInput
from backend.schemas.agents.analysis import IntentTranslationAgentInput

# ---------------------------------------------------------------------------
# Edit these to change what gets tested
# ---------------------------------------------------------------------------

PROMPT = """\
You are a helpful assistant for a social media marketing tool. \
Generate an engaging Instagram caption for the user's product photo \
that includes relevant hashtags and a call to action.
"""

QA_PAIRS = [
    QAPair(
        question_text="What type of product or brand is this for?",
        answer_text="A sustainable athleisure brand targeting millennials.",
    ),
    QAPair(
        question_text="What tone should the caption have?",
        answer_text="Energetic and motivational, but not pushy.",
    ),
    QAPair(
        question_text="Are there any specific constraints on the output format?",
        answer_text="Max 2200 characters, must end with a clear CTA and 5–10 hashtags.",
    ),
]

PROJECT_DEFINITION = (
    "An AI marketing tool that generates on-brand Instagram captions for a sustainable "
    "athleisure brand. It takes a product photo description and brand guidelines as input "
    "and produces a caption with a CTA and 5–10 targeted hashtags."
)

# ---------------------------------------------------------------------------


async def main() -> None:
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    with open(PROJECT_ROOT / "taxonomy.json") as f:
        taxonomy = json.load(f)

    engine = _get_engine()

    async with AsyncSession(engine) as db:
        print("── Retrieval agent ─────────────────────────────────────────")
        retrieval_input = RetrievalAgentInput(
            original_prompt=PROMPT,
            qa_pairs=QA_PAIRS,
            project_summary=PROJECT_DEFINITION,
            taxonomy=taxonomy,
        )
        retrieval_output = await retrieval_agent.run(client, retrieval_input, db, settings)
        print(f"Retrieved {len(retrieval_output.retrieved_docs)} docs")
        print(f"Category: {retrieval_output.category}")
        print(f"Tags: {retrieval_output.concept_tags}")

        print("\n── Intent translation agent ────────────────────────────────")
        translation_input = IntentTranslationAgentInput(
            original_prompt=PROMPT,
            qa_pairs=QA_PAIRS,
            retrieved_documents=retrieval_output.retrieved_docs,
            project_definition=PROJECT_DEFINITION,
            past_translations=[],
        )
        translation_output = await analysis_agent.run(client, translation_input)
        t = translation_output.intent_translation

        print(f"\nWhat it instructs:\n  {t.what_the_prompt_instructs}")
        print(f"\nAssumptions made:")
        for a in t.assumptions_made:
            print(f"  • {a}")
        print(f"\nPotential gaps:")
        for g in t.potential_gaps:
            print(f"  • {g}")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
