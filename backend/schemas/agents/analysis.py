from pydantic import BaseModel

from backend.schemas.agents.retrieval import QAPair, RetrievedDocResult


class IntentTranslation(BaseModel):
    what_the_prompt_instructs: str
    assumptions_made: list[str]
    potential_gaps: list[str]


class IntentTranslationAgentInput(BaseModel):
    original_prompt: str
    qa_pairs: list[QAPair]
    retrieved_documents: list[RetrievedDocResult]
    project_definition: str | None
    past_translations: list[str]


class IntentTranslationAgentOutput(BaseModel):
    intent_translation: IntentTranslation
