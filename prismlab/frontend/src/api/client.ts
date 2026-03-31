import type { Hero, SuggestHeroRequest, SuggestHeroResponse } from "../types/hero";
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
  suggestHero: (req: SuggestHeroRequest) =>
    postJson<SuggestHeroRequest, SuggestHeroResponse>("/suggest-hero", req),
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
  setEngineBudget: async (budget: number): Promise<EngineBudget> => {
    const res = await fetch(`${API_BASE}/settings/budget`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget }),
    });
    if (!res.ok) throw new Error(`Failed to set budget: ${res.status}`);
    return res.json();
  },
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

  /**
   * SSE streaming recommendation.
   * Returns an AbortController to cancel the stream.
   * Calls onEvent for each SSE event: rules, phases, enrichment, done, error.
   */
  recommendStream: (
    req: RecommendRequest,
    onEvent: (type: string, data: unknown) => void,
  ): AbortController => {
    const mode = localStorage.getItem("prismlab_engine_mode") as
      | "fast"
      | "auto"
      | "deep"
      | null;
    const enriched: RecommendRequest = {
      ...req,
      mode: req.mode ?? mode ?? undefined,
    };
    const controller = new AbortController();

    fetch(`${API_BASE}/recommend/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(enriched),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          onEvent("error", { message: `API error: ${response.status}` });
          return;
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events from buffer
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? ""; // keep incomplete line in buffer

          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ") && currentEvent) {
              try {
                const data = JSON.parse(line.slice(6));
                onEvent(currentEvent, data);
              } catch {
                /* ignore parse errors */
              }
              currentEvent = "";
            }
          }
        }
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") {
          onEvent("error", { message: err.message ?? "Stream failed" });
        }
      });

    return controller;
  },
};
