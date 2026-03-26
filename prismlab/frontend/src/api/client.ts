import type { Hero } from "../types/hero";
import type {
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
  recommend: (req: RecommendRequest) =>
    postJson<RecommendRequest, RecommendResponse>("/recommend", req),
  getDataFreshness: () => fetchJson<DataFreshness>("/data-freshness"),
  parseScreenshot: (req: ScreenshotParseRequest) =>
    postJson<ScreenshotParseRequest, ScreenshotParseResponse>(
      "/parse-screenshot",
      req,
    ),
};
