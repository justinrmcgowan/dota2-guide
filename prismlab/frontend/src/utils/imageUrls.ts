const HERO_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes";
const ITEM_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items";

export const heroImageUrl = (heroSlug: string) => `${HERO_CDN}/${heroSlug}.png`;
export const heroIconUrl = (heroSlug: string) => `${HERO_CDN}/icons/${heroSlug}.png`;
export const itemImageUrl = (itemSlug: string) => `${ITEM_CDN}/${itemSlug}.png`;

export const heroSlugFromInternal = (internalName: string) =>
  internalName.replace("npc_dota_hero_", "");
