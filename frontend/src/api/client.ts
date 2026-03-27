const API_BASE = 'http://localhost:8000/api/v1';

type RequestOptions = {
  headers?: Record<string, string>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const bodyText = await response.text();
  if (!bodyText) {
    return undefined as T;
  }
  return JSON.parse(bodyText) as T;
}

export async function apiGet<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, { headers: options?.headers });
}

export async function apiPost<T>(path: string, payload?: unknown, options?: RequestOptions): Promise<T> {
  const body = payload === undefined
    ? undefined
    : typeof payload === 'string'
      ? payload
      : JSON.stringify(payload);

  return request<T>(path, {
    method: 'POST',
    body,
    headers: options?.headers,
  });
}

export async function apiDelete(path: string, options?: RequestOptions): Promise<void> {
  await request(path, {
    method: 'DELETE',
    headers: options?.headers,
  });
}

