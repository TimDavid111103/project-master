// ── Shared ───────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// ── Project plan ──────────────────────────────────────────────────────────────

export interface ProjectPlan {
  vision: string;
  target_audience: string;
  problem_addressed: string;
  mvp_scope: string;
}

// ── Tech stack ────────────────────────────────────────────────────────────────

export interface TechStackItem {
  name: string;
  category: string;
  rationale: string;
}

export interface TechStack {
  mvp: TechStackItem[];
  full_product: TechStackItem[];
}

// ── Pipeline API ──────────────────────────────────────────────────────────────

export interface PipelineChatRequest {
  user_message: string;
  conversation_history: ChatMessage[];
}

export interface PipelineChatResponse {
  agent_message: string;
  is_complete: boolean;
  project_plan: ProjectPlan | null;
}

export interface PipelineAnalyzeRequest {
  project_id: string;
  project_plan: ProjectPlan;
}

export interface PipelineAnalyzeResponse {
  project_plan: ProjectPlan;
  tech_stack: TechStack;
}

// ── Projects API ──────────────────────────────────────────────────────────────

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
  is_complete: boolean;
  created_at: string;
}

export interface ProjectDetailResponse {
  project_id: string;
  name: string;
  rough_idea: string;
  is_complete: boolean;
  project_plan: ProjectPlan | null;
  tech_stack: TechStack | null;
  created_at: string;
}
