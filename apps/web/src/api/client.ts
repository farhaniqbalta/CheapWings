import { errorMessage } from "./errors";
import { getOwnerToken } from "./session";
import type {
  Capabilities,
  Created,
  HTTPValidationError,
  Job,
  Results,
  SearchRequest,
  SortMode,
  WorkerPool,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");


export class ApiError extends Error {
  status: number;
  detail: HTTPValidationError | null;

  constructor(status: number, message: string, detail: HTTPValidationError | null = null) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const ownerToken = getOwnerToken();
  if (ownerToken) headers.set("Authorization", `Bearer ${ownerToken}`);

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail: HTTPValidationError | null = null;
    try {
      detail = await response.json();
    } catch {
      // Non-JSON error body (e.g. plain-text 429/410); leave detail null.
    }
    const message = errorMessage(detail, `${response.status} ${response.statusText}`);
    throw new ApiError(response.status, message, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string; service: string }>("/api/v1/health"),

  capabilities: () => request<Capabilities>("/api/v1/capabilities"),

  workerPool: () => request<WorkerPool>("/api/v1/worker/pool"),

  createSearch: (body: SearchRequest) =>
    request<Created>("/api/v1/searches", { method: "POST", body: JSON.stringify(body) }),

  getJob: (jobId: string) => request<Job>(`/api/v1/searches/${encodeURIComponent(jobId)}`),

  getResults: (jobId: string, sort: SortMode, cursor?: string | null, limit = 50) => {
    const params = new URLSearchParams({ sort, limit: String(limit) });
    if (cursor) params.set("cursor", cursor);
    return request<Results>(`/api/v1/searches/${encodeURIComponent(jobId)}/results?${params.toString()}`);
  },

  cancelSearch: (jobId: string) =>
    request<Job>(`/api/v1/searches/${encodeURIComponent(jobId)}/cancel`, { method: "POST" }),
};

export const TERMINAL_STATUSES = new Set(["completed", "partial", "failed", "cancelled"]);
