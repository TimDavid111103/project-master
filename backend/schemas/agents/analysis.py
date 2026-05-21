from typing import Literal

from pydantic import BaseModel

from backend.schemas.agents.retrieval import QAPair, RetrievedDocResult


class DimensionGrade(BaseModel):
    grade: Literal["F", "D", "C", "B", "A", "S"]
    explanation: str


class PromptAnalysis(BaseModel):
    intent_accuracy: DimensionGrade
    technical_language: DimensionGrade
    standards_alignment: DimensionGrade


class AnalysisAgentInput(BaseModel):
    original_prompt: str
    qa_pairs: list[QAPair]
    retrieved_documents: list[RetrievedDocResult]
    project_summary: str | None
    past_analyses: list[str]


class AnalysisAgentOutput(BaseModel):
    analysis: PromptAnalysis
