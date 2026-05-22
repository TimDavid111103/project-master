export interface ClarifyingQuestion {
  question_id: string;
  question_text: string;
  rationale: string;
}

export interface UserAnswer {
  question_id: string;
  answer_text: string;
}

// ── Project types ────────────────────────────────────────────────────────────

export interface CreateProjectRequest {
  name: string;
  rough_idea: string;
}

export interface CreateProjectResponse {
  project_id: string;
  name: string;
  rough_idea: string;
  created_at: string;
}

export interface ProjectListItem {
  project_id: string;
  name: string;
  rough_idea: string;
  definition: string | null;
  created_at: string;
}

export interface IntentTranslation {
  what_the_prompt_instructs: string;
  assumptions_made: string[];
  potential_gaps: string[];
}

export interface PromptSessionRecord {
  session_id: string;
  original_prompt: string;
  intent_translation: IntentTranslation;
  created_at: string;
}

export interface ProjectHistoryResponse {
  project_id: string;
  name: string;
  rough_idea: string;
  definition: string | null;
  created_at: string;
  sessions: PromptSessionRecord[];
}

// ── Project setup types ──────────────────────────────────────────────────────

export interface ProjectSetupContext {
  project_id: string;
  rough_idea: string;
  questions: ClarifyingQuestion[];
}

export interface ProjectSetupStartResponse {
  setup_context: ProjectSetupContext;
  questions: ClarifyingQuestion[];
}

export interface ProjectSetupRespondRequest {
  setup_context: ProjectSetupContext;
  answers: UserAnswer[];
}

export interface ProjectSetupRespondResponse {
  project_id: string;
  project_definition: string;
}

// ── Session types ────────────────────────────────────────────────────────────

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

export interface RetrievedDocResult {
  doc_id: string;
  content: string;
  similarity_score: number;
  chunk_level: string;
  parent_id: string | null;
}

export interface SessionRespondResponse {
  original_prompt: string;
  intent_translation: IntentTranslation;
  retrieved_documents: RetrievedDocResult[];
}
