import type {
  SessionRespondRequest,
  SessionRespondResponse,
  SessionStartRequest,
  SessionStartResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response.json() as Promise<TRes>;
}

export const api = {
  sessionStart: (body: SessionStartRequest): Promise<SessionStartResponse> =>
    post("/api/v1/session/start", body),

  sessionRespond: (body: SessionRespondRequest): Promise<SessionRespondResponse> =>
    post("/api/v1/session/respond", body),
};
