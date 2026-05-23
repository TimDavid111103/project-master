import type {
  CreateProjectRequest,
  CreateProjectResponse,
  PipelineAnalyzeRequest,
  PipelineAnalyzeResponse,
  PipelineChatRequest,
  PipelineChatResponse,
  ProjectDetailResponse,
  ProjectListItem,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<TRes>(
  path: string,
  options: RequestInit = {}
): Promise<TRes> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response.json() as Promise<TRes>;
}

function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  return request<TRes>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

function get<TRes>(path: string): Promise<TRes> {
  return request<TRes>(path, { method: "GET" });
}

export const api = {
  // Projects
  listProjects: (): Promise<ProjectListItem[]> =>
    get("/api/v1/projects"),

  createProject: (body: CreateProjectRequest): Promise<CreateProjectResponse> =>
    post("/api/v1/projects", body),

  getProject: (projectId: string): Promise<ProjectDetailResponse> =>
    get(`/api/v1/projects/${projectId}`),

  // Pipeline
  pipelineChat: (body: PipelineChatRequest): Promise<PipelineChatResponse> =>
    post("/api/v1/pipeline/chat", body),

  pipelineAnalyze: (body: PipelineAnalyzeRequest): Promise<PipelineAnalyzeResponse> =>
    post("/api/v1/pipeline/analyze", body),
};
