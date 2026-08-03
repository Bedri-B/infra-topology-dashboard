import type { LayoutResponse, StatusResponse, TopologyInput } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    throw new Error(detail || `Request to ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

/** GET /api/v1/topology/layout -- the bundled sample topology's layout. */
export function fetchSampleLayout(): Promise<LayoutResponse> {
  return request<LayoutResponse>("/api/v1/topology/layout");
}

/** GET /api/v1/topology/status -- current simulated status per node. */
export function fetchStatus(): Promise<StatusResponse> {
  return request<StatusResponse>("/api/v1/topology/status");
}

/** POST /api/v1/topology/layout -- layout for an arbitrary topology (not persisted). */
export function fetchLayoutFor(topology: TopologyInput): Promise<LayoutResponse> {
  return request<LayoutResponse>("/api/v1/topology/layout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(topology),
  });
}
