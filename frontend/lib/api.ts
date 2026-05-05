const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Auth ---
export const auth = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string }>("/auth/me"),
};

// --- Bots ---
export type Bot = {
  id: string;
  name: string;
  exchange: string;
  symbol: string;
  trade_type: string;
  strategy: string;
  strategy_params: Record<string, unknown>;
  budget: number;
  stop_loss_pct: number;
  status: "running" | "stopped" | "error";
  error_message: string | null;
  last_executed_at: string | null;
  created_at: string;
};

export type BotCreate = {
  name: string;
  exchange: string;
  symbol: string;
  trade_type: string;
  strategy: string;
  strategy_params: Record<string, unknown>;
  budget: number;
  stop_loss_pct: number;
};

export type Performance = {
  bot_id: string;
  total_pnl: number;
  trade_count: number;
  win_count: number;
  win_rate: number;
};

export const bots = {
  list: () => request<Bot[]>("/bots"),
  create: (data: BotCreate) =>
    request<Bot>("/bots", { method: "POST", body: JSON.stringify(data) }),
  start: (id: string) => request<Bot>(`/bots/${id}/start`, { method: "POST" }),
  stop: (id: string) => request<Bot>(`/bots/${id}/stop`, { method: "POST" }),
  delete: (id: string) => request<void>(`/bots/${id}`, { method: "DELETE" }),
  performance: (id: string) => request<Performance>(`/bots/${id}/performance`),
};

// --- Exchange Keys ---
export type ExchangeKey = {
  id: string;
  exchange: string;
  created_at: string;
};

export const exchanges = {
  list: () => request<ExchangeKey[]>("/exchanges"),
  add: (exchange: string, api_key: string, api_secret: string) =>
    request<ExchangeKey>("/exchanges", {
      method: "POST",
      body: JSON.stringify({ exchange, api_key, api_secret }),
    }),
  remove: (id: string) => request<void>(`/exchanges/${id}`, { method: "DELETE" }),
};
