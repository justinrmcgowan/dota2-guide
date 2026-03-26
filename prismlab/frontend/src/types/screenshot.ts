/** TypeScript interfaces matching backend Pydantic schemas for screenshot parsing */

export interface ParsedItem {
  display_name: string;
  internal_name: string;
  confidence: "high" | "medium" | "low";
}

export interface ParsedHero {
  hero_name: string;
  hero_id: number | null;
  internal_name: string | null;
  items: ParsedItem[];
  kills: number | null;
  deaths: number | null;
  assists: number | null;
  level: number | null;
}

export interface ScreenshotParseRequest {
  image_base64: string;
  media_type: string;
}

export interface ScreenshotParseResponse {
  heroes: ParsedHero[];
  error: string | null;
  message: string | null;
  latency_ms: number | null;
}
