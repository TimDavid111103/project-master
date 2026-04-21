from pydantic import BaseModel


class ClarifyingQuestion(BaseModel):
    question_id: str
    question_text: str
    rationale: str


class UserAnswer(BaseModel):
    question_id: str
    answer_text: str
