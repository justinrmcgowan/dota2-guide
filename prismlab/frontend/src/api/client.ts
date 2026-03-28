import type { Hero } from "../types/hero";
import type { LiveMatchResponse } from "../types/livematch";
import type {
  MatchLogPayload,
  MatchHistoryResponse,
  MatchStatsResponse,
} from "../types/matchLog";
import type {
  EngineBudget,
  RecommendRequest,
  RecommendResponse,
} from "../types/recommendation";
import type {
  ScreenshotParseRequest,
  ScreenshotParseResponse,
} from "../types/screenshot";

const API_BASE = "/api";

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function postJson<TReq, TRes>(url: string, body: TReq): Promise<TRes> {
  const response = await fetch(`${API_BASE}${url}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      const seconds = retryAfter ? parseInt(retryAfter, 10) : 10;
      throw new Error(
        `Please wait ${seconds} seconds before requesting again.`,
      );
    }
    if (response.status === 422) {
      const detail = await response.json().catch(() => null);
      const msg =
        detail?.detail?.[0]?.msg ?? detail?.detail ?? "Validation error";
      throw new Error(String(msg));
    }
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export interface DataFreshness {
  last_refresh: string | null;
  heroes_updated: number;
  items_updated: number;
}

export const api = {
  getHeroes: () => fetchJson<Hero[]>("/heroes"),
  recommend: (req: RecommendRequest) => {
    // Auto-inject engine mode from localStorage if not already set on the request
    const mode = localStorage.getItem("prismlab_engine_mode") as
      | "fast"
      | "auto"
      | "deep"
      | null;
    const enriched: RecommendRequest = { ...req, mode: req.mode ?? mode ?? undefined };
    return postJson<RecommendRequest, RecommendResponse>("/recommend", enriched);
  },
  getDataFreshness: () => fetchJson<DataFreshness>("/data-freshness"),
  parseScreenshot: (req: ScreenshotParseRequest) =>
    postJson<ScreenshotParseRequest, ScreenshotParseResponse>(
      "/parse-screenshot",
      req,
    ),
  getLiveMatch: (accountId: number) =>
    fetchJson<LiveMatchResponse | null>(`/live-match/${accountId}`),
  getSettingsDefaults: () =>
    fetchJson<{ steam_id: string | null }>("/settings/defaults"),
  getEngineBudget: () => fetchJson<EngineBudget>("/settings/budget"),
  logMatch: (payload: MatchLogPayload) =>
    postJson<MatchLogPayload, { status: string; id: number; follow_rate: number }>(
      "/match-log",
      payload,
    ),
  getMatchHistory: (params?: {
    hero_id?: number;
    result?: string;
    mode?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.hero_id) qs.set("hero_id", String(params.hero_id));
    if (params?.result) qs.set("result", params.result);
    if (params?.mode) qs.set("mode", params.mode);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return fetchJson<MatchHistoryResponse>(
      `/match-history${query ? `?${query}` : ""}`,
    );
  },
  getMatchStats: () => fetchJson<MatchStatsResponse>("/match-stats"),
};
