import type { ClaimDetail, ClaimSummary, Handler } from "./types";

async function readError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return body.detail;
  }
  return `Request failed (${String(response.status)})`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as T;
}

export function fetchClaims(): Promise<ClaimSummary[]> {
  return requestJson<ClaimSummary[]>("/api/claims");
}

export function fetchClaim(claimId: string): Promise<ClaimDetail> {
  return requestJson<ClaimDetail>(`/api/claims/${claimId}`);
}

export function workClaim(claimId: string): Promise<ClaimDetail> {
  return requestJson<ClaimDetail>(`/api/claims/${claimId}/work`, {
    method: "POST",
  });
}

export function signOffClaim(
  claimId: string,
  handlerId: string,
): Promise<ClaimDetail> {
  return requestJson<ClaimDetail>(`/api/claims/${claimId}/sign-off`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handler_id: handlerId }),
  });
}

export function fetchHandlers(): Promise<Handler[]> {
  return requestJson<Handler[]>("/api/handlers");
}

export async function fetchInstructions(): Promise<string> {
  const response = await fetch("/api/instructions");
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.text();
}
