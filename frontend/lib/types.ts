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
}

export interface SessionStartRequest {
  original_prompt: string;
}

export interface SessionStartResponse {
  session_context: SessionContext;
  questions: ClarifyingQuestion[];
}

export interface SessionRespondRequest {
  session_context: SessionContext;
  answers: UserAnswer[];
}

export interface ReformulatedQuery {
  category: string;
  concept_tags: string[];
  query_text: string;
}

export interface RetrievedDocument {
  doc_id: string;
  content: string;
  similarity_score: number;
}

export interface SessionRespondResponse {
  original_prompt: string;
  revised_prompt: string;
  analysis: string;
  reformulated_query: ReformulatedQuery;
  retrieved_documents: RetrievedDocument[];
}
