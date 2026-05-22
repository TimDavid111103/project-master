import uuid

from pydantic import BaseModel

from backend.schemas.agents.retrieval import QAPair


class ProjectMemory(BaseModel):
    project_id: uuid.UUID
    project_definition: str | None       # None until setup completes
    past_raw_prompts: list[str]
    past_qa_pairs: list[QAPair]
    past_translations: list[str]         # serialized IntentTranslation strings
    previous_questions: list[str]        # all question_text values ever asked in this project
