const env = import.meta as unknown as { env?: { VITE_API_URL?: string } };

export const API_BASE_URL = (env.env?.VITE_API_URL || 'http://localhost:5050').replace(/\/$/, '');

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }

  return data as T;
}

export function getHealth() {
  return requestJson<{
    status: string;
    provider: string;
    model: string;
    groq_api_key_set: boolean;
  }>('/api/health');
}

export function queryAssistant(query: string, maxIterations = 10) {
  return requestJson<{
    success: boolean;
    response: string;
    tool_calls: Array<{ tool: string; input: unknown; result: unknown }>;
    error?: string;
  }>('/api/query', {
    method: 'POST',
    body: JSON.stringify({ query, max_iterations: maxIterations }),
  });
}

export function resetAssistant() {
  return requestJson<{ success: boolean }>('/api/reset', { method: 'POST' });
}

export function runTool(tool: 'read' | 'list' | 'write' | 'search', params: Record<string, unknown>) {
  return requestJson<unknown>(`/api/tools/${tool}`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
