export interface ClarifyingQuestion {
  question_id: string;
  question_text: string;
  rationale: string;
}

export interface UserAnswer {
  question_id: string;
  answer_text: string;
}

export interface SessionContext {
  original_prompt: string;
  questions: ClarifyingQuestion[];
  project_id: string;
}

export interface SessionStartRequest {
  original_prompt: string;
  project_id: string;
}

export interface SessionStartResponse {
  session_context: SessionContext;
  questions: ClarifyingQuestion[];
}

export interface SessionRespondRequest {
  session_context: SessionContext;
  answers: UserAnswer[];
}

export interface DimensionGrade {
  grade: "F" | "D" | "C" | "B" | "A" | "S";
  explanation: string;
}

export interface PromptAnalysis {
  intent_accuracy: DimensionGrade;
  technical_language: DimensionGrade;
  standards_alignment: DimensionGrade;
}

export interface RetrievedDocResult {
  doc_id: string;
  content: string;
  similarity_score: number;
  chunk_level: string;
  parent_id: string | null;
}

export interface SessionRespondResponse {
  original_prompt: string;
  analysis: PromptAnalysis;
  retrieved_documents: RetrievedDocResult[];
}

export interface CreateProjectRequest {
  name: string;
  summary: string;
}

export interface CreateProjectResponse {
  project_id: string;
  name: string;
  summary: string;
  created_at: string;
}
