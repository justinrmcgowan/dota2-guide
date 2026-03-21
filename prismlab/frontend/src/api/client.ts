import type { Hero } from "../types/hero";
import type { Item } from "../types/item";

const API_BASE = "/api";

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  getHeroes: () => fetchJson<Hero[]>("/heroes"),
  getHero: (id: number) => fetchJson<Hero>(`/heroes/${id}`),
  getItems: () => fetchJson<Item[]>("/items"),
  getItem: (id: number) => fetchJson<Item>(`/items/${id}`),
};
