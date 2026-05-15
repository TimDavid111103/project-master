"""Offline script: analyze corpus documents and propose a taxonomy.json.

Usage:
    uv run python scripts/taxonomy_discovery.py --corpus-dir corpus/ --output taxonomy.json

This is a one-time operation. Review the output manually before running ingest.py.
"""
import argparse
import asyncio
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import anthropic
from pydantic import BaseModel

from backend.config import get_settings


class TaxonomyProposal(BaseModel):
    taxonomy: dict[str, list[str]]


SYSTEM_PROMPT = """\
You are an expert at building knowledge taxonomies for RAG systems.
Analyze the provided document excerpts and propose a two-level taxonomy:
- Top-level keys: broad categories (5-10)
- Values: lists of specific concept tags per category (3-8 each)

Output only valid JSON matching the schema. Use snake_case for all keys and tags.\
"""


async def discover_taxonomy(corpus_dir: pathlib.Path, output_path: pathlib.Path) -> None:
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    corpus_files = list(corpus_dir.glob("**/*.txt")) + list(corpus_dir.glob("**/*.md"))
    if not corpus_files:
        print(f"No .txt or .md files found in {corpus_dir}. Add documents and retry.")
        return

    excerpts = []
    for path in corpus_files[:20]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        excerpts.append(f"--- {path.name} ---\n{text[:2000]}")

    combined = "\n\n".join(excerpts)
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": combined}],
        tools=[
            {
                "name": "output_taxonomy",
                "description": "Output the proposed taxonomy as structured JSON.",
                "input_schema": TaxonomyProposal.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_taxonomy"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    proposal = TaxonomyProposal.model_validate(tool_block.input)

    output_path.write_text(json.dumps(proposal.taxonomy, indent=2))
    print(f"Taxonomy written to {output_path}. Review and edit before running ingest.py.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="corpus", type=pathlib.Path)
    parser.add_argument("--output", default="taxonomy.json", type=pathlib.Path)
    args = parser.parse_args()
    asyncio.run(discover_taxonomy(args.corpus_dir, args.output))
