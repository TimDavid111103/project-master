from pydantic import BaseModel


class QAPair(BaseModel):
    question_text: str
    answer_text: str


class RetrievedDocResult(BaseModel):
    doc_id: str
    content: str
    similarity_score: float
    chunk_level: str
    parent_id: str | None


class RetrievalAgentInput(BaseModel):
    original_prompt: str
    qa_pairs: list[QAPair]
    project_summary: str | None
    taxonomy: dict


class RetrievalAgentOutput(BaseModel):
    retrieved_docs: list[RetrievedDocResult]
    category: str
    concept_tags: list[str]
