import type {
  CreateProjectRequest,
  CreateProjectResponse,
  ProjectHistoryResponse,
  ProjectListItem,
  ProjectSetupRespondRequest,
  ProjectSetupRespondResponse,
  ProjectSetupStartResponse,
  SessionRespondRequest,
  SessionRespondResponse,
  SessionStartRequest,
  SessionStartResponse,
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

  projectHistory: (projectId: string): Promise<ProjectHistoryResponse> =>
    get(`/api/v1/projects/${projectId}/history`),

  // Project setup
  setupStart: (projectId: string): Promise<ProjectSetupStartResponse> =>
    post(`/api/v1/projects/${projectId}/setup/start`, {}),

  setupRespond: (
    projectId: string,
    body: ProjectSetupRespondRequest
  ): Promise<ProjectSetupRespondResponse> =>
    post(`/api/v1/projects/${projectId}/setup/respond`, body),

  // Prompt session
  sessionStart: (body: SessionStartRequest): Promise<SessionStartResponse> =>
    post("/api/v1/session/start", body),

  sessionRespond: (
    body: SessionRespondRequest
  ): Promise<SessionRespondResponse> =>
    post("/api/v1/session/respond", body),
};
