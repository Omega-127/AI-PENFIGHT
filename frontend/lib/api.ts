// Single typed API client — every network call to the backend routes
// through here, per ARCHITECTURE.md §4 ("Route all network calls through
// a single typed API client so headers, base URL, and error handling
// live in one place.")

import { API_BASE_URL, API_VERSION_PATH } from "./constants";
import type { AnalyzeRequest, AnalyzeResponse, ApiError } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${API_VERSION_PATH}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    throw body ?? {
      success: false,
      error: { code: "UNKNOWN_ERROR", message: "Something went wrong." },
    };
  }

  return res.json() as Promise<T>;
}

export function analyze(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getHistory(limit = 20, cursor?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request(`/history?${params.toString()}`);
}

export function getPerformance() {
  return request("/performance");
}
