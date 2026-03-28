const STEAM_ID_64_BASE = 76561197960265728n;

export function steamId64ToAccountId(steamId64: string): number {
  const id64 = BigInt(steamId64);
  return Number(id64 - STEAM_ID_64_BASE);
}

export function accountIdToSteamId64(accountId: number): string {
  return String(STEAM_ID_64_BASE + BigInt(accountId));
}

export function isValidSteamId(input: string): boolean {
  try {
    if (!/^\d{17}$/.test(input)) return false; // Must be 17 digits
    const accountId = steamId64ToAccountId(input);
    return accountId > 0 && accountId < 2 ** 32;
  } catch {
    return false;
  }
}
