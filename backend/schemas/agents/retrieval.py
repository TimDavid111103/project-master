from pydantic import BaseModel

from backend.schemas.agents.ideation import ProjectPlan


class RetrievedDocResult(BaseModel):
    doc_id: str
    content: str
    similarity_score: float


class RetrievalAgentInput(BaseModel):
    project_plan: ProjectPlan


class RetrievalAgentOutput(BaseModel):
    retrieved_docs: list[RetrievedDocResult] = []
