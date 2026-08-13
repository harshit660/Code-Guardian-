import type { Analysis, AnalysisDetail, Repository } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

let token = localStorage.getItem("codeguardian_token") || "";
export const auth = {
  get loggedIn() { return Boolean(token); },
  set(next: string) { token = next; localStorage.setItem("codeguardian_token", next); },
  clear() { token = ""; localStorage.removeItem("codeguardian_token"); },
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  authenticate: (email: string, password: string, register = false) => request<{ access_token: string }>(`/auth/${register ? "register" : "token"}`, { method: "POST", body: JSON.stringify({ email, password }) }),
  repositories: () => request<Repository[]>("/repositories"),
  createRepository: (github_owner: string, github_name: string, default_branch: string) => request<Repository>("/repositories", { method: "POST", body: JSON.stringify({ github_owner, github_name, default_branch }) }),
  branches: (id: string) => request<string[]>(`/repositories/${id}/branches`),
  analyses: (repositoryId: string) => request<Analysis[]>(`/analyses/repositories/${repositoryId}`),
  trigger: (repositoryId: string, branch: string) => request<Analysis>(`/analyses/repositories/${repositoryId}`, { method: "POST", body: JSON.stringify({ branch }) }),
  analysis: (id: string) => request<AnalysisDetail>(`/analyses/${id}`),
  publishReview: (analysisId: string, pullNumber: number, findingIds: string[]) => request<{ submitted: number }>(`/analyses/${analysisId}/pull-request-review`, { method: "POST", body: JSON.stringify({ pull_number: pullNumber, finding_ids: findingIds }) }),
};

