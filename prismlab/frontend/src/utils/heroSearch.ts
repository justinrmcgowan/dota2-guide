import Fuse from "fuse.js";
import type { Hero } from "../types/hero";

const fuseOptions: Fuse.IFuseOptions<Hero> = {
  keys: [
    { name: "localized_name", weight: 2 },
    { name: "name", weight: 1.5 },
    { name: "roles", weight: 0.5 },
  ],
  threshold: 0.4,
  distance: 200,
  minMatchCharLength: 1,
  ignoreLocation: true,
  findAllMatches: true,
};

export function createHeroSearcher(heroes: Hero[]): Fuse<Hero> {
  return new Fuse(heroes, fuseOptions);
}

/**
 * Search heroes using a hybrid approach:
 * 1. Substring match on localized_name (catches abbreviations like "am" -> "Anti-Mage")
 * 2. Initials match (catches "am" -> "Anti-Mage", "cm" -> "Crystal Maiden")
 * 3. Fuse.js fuzzy match (catches typos like "anit" -> "Anti-Mage")
 * Results are deduplicated, with substring/initial matches ranked first.
 */
export function searchHeroes(fuse: Fuse<Hero>, query: string): Hero[] {
  const trimmed = query.trim();
  if (!trimmed) return [];

  const lower = trimmed.toLowerCase();
  const allHeroes = fuse.getIndex().docs as unknown as Hero[];

  // Substring matches on localized_name
  const substringMatches = allHeroes.filter((h) =>
    h.localized_name.toLowerCase().includes(lower)
  );

  // Initials match: "am" matches "Anti-Mage", "cm" matches "Crystal Maiden"
  const initialMatches = allHeroes.filter((h) => {
    const initials = h.localized_name
      .split(/[\s-]+/)
      .map((w) => w[0]?.toLowerCase() ?? "")
      .join("");
    return initials.startsWith(lower);
  });

  // Fuse.js fuzzy matches
  const fuseMatches = fuse.search(trimmed).map((r) => r.item);

  // Deduplicate: substring/initials first, then fuse results
  const seen = new Set<number>();
  const results: Hero[] = [];

  for (const hero of [...substringMatches, ...initialMatches, ...fuseMatches]) {
    if (!seen.has(hero.id)) {
      seen.add(hero.id);
      results.push(hero);
    }
  }

  return results;
}
