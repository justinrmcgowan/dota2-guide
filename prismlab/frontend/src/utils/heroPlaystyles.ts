/**
 * Default hero playstyle map keyed by "{hero_id}-{role}".
 *
 * Each key is a string of the form "1-1" where the first number is the hero's
 * OpenDota numeric ID and the second is the role/position (1-5).  Values are
 * valid playstyle strings from PLAYSTYLE_OPTIONS in constants.ts.
 *
 * If a hero+role combination is not present in this map, the consumer should
 * fall back to letting the user choose manually from PLAYSTYLE_OPTIONS[role].
 */
export const HERO_PLAYSTYLE_MAP: Record<string, string> = {
  // 1: Anti-Mage
  "1-1": "Farm-first",

  // 2: Axe
  "2-3": "Initiator",

  // 3: Bane
  "3-5": "Save",

  // 5: Crystal Maiden
  "5-5": "Lane-protector",

  // 6: Drow Ranger
  "6-1": "Farm-first",

  // 7: Earthshaker
  "7-4": "Roamer",

  // 8: Juggernaut
  "8-1": "Fighting",

  // 9: Mirana
  "9-2": "Tempo",
  "9-4": "Roamer",

  // 10: Morphling
  "10-1": "Farm-first",

  // 11: Shadow Fiend
  "11-2": "Tempo",

  // 12: Phantom Lancer
  "12-1": "Farm-first",

  // 13: Puck
  "13-2": "Tempo",

  // 14: Pudge
  "14-4": "Roamer",

  // 15: Razor
  "15-2": "Tempo",

  // 16: Sand King
  "16-3": "Initiator",
  "16-4": "Roamer",

  // 17: Storm Spirit
  "17-2": "Ganker",

  // 18: Sven
  "18-1": "Fighting",

  // 19: Tiny
  "19-2": "Ganker",
  "19-3": "Initiator",

  // 20: Vengeful Spirit
  "20-4": "Lane-dominator",
  "20-5": "Save",

  // 21: Windranger
  "21-2": "Tempo",

  // 22: Zeus
  "22-2": "Tempo",
  "22-4": "Greedy",

  // 23: Kunkka
  "23-2": "Tempo",

  // 25: Lina
  "25-2": "Tempo",
  "25-4": "Lane-dominator",

  // 26: Lion
  "26-4": "Roamer",
  "26-5": "Lane-protector",

  // 27: Shadow Shaman
  "27-5": "Lane-protector",

  // 28: Slardar
  "28-3": "Initiator",

  // 29: Tidehunter
  "29-3": "Frontline",

  // 30: Witch Doctor
  "30-5": "Lane-protector",

  // 31: Lich
  "31-5": "Lane-protector",

  // 32: Riki
  "32-1": "Aggressive",
  "32-4": "Roamer",

  // 33: Enigma
  "33-3": "Greedy",

  // 35: Sniper
  "35-1": "Farm-first",
  "35-2": "Greedy",

  // 36: Necrophos
  "36-2": "Tempo",
  "36-3": "Frontline",

  // 37: Warlock
  "37-5": "Lane-protector",

  // 38: Beastmaster
  "38-3": "Aura-carrier",

  // 39: Queen of Pain
  "39-2": "Ganker",

  // 40: Venomancer
  "40-3": "Aura-carrier",
  "40-4": "Lane-dominator",

  // 41: Faceless Void
  "41-1": "Farm-first",

  // 42: Wraith King
  "42-1": "Fighting",
  "42-3": "Frontline",

  // 43: Death Prophet
  "43-2": "Tempo",

  // 44: Phantom Assassin
  "44-1": "Aggressive",

  // 45: Pugna
  "45-2": "Tempo",
  "45-5": "Save",

  // 46: Templar Assassin
  "46-2": "Tempo",

  // 47: Viper
  "47-2": "Tempo",
  "47-3": "Frontline",

  // 48: Luna
  "48-1": "Farm-first",

  // 49: Dragon Knight
  "49-2": "Tempo",
  "49-3": "Frontline",

  // 50: Dazzle
  "50-5": "Save",

  // 51: Clockwerk
  "51-3": "Initiator",
  "51-4": "Roamer",

  // 52: Leshrac
  "52-2": "Tempo",

  // 53: Nature's Prophet
  "53-3": "Split-push",

  // 54: Lifestealer
  "54-1": "Fighting",

  // 55: Dark Seer
  "55-3": "Aura-carrier",

  // 56: Clinkz
  "56-1": "Aggressive",
  "56-2": "Ganker",

  // 57: Omniknight
  "57-3": "Frontline",
  "57-5": "Save",

  // 58: Enchantress
  "58-4": "Lane-dominator",
  "58-5": "Greedy",

  // 59: Huskar
  "59-2": "Aggressive",

  // 60: Night Stalker
  "60-3": "Initiator",

  // 61: Broodmother
  "61-2": "Greedy",
  "61-3": "Greedy",

  // 62: Bounty Hunter
  "62-4": "Roamer",

  // 63: Weaver
  "63-1": "Aggressive",

  // 64: Jakiro
  "64-5": "Lane-protector",

  // 65: Batrider
  "65-3": "Initiator",

  // 66: Chen
  "66-4": "Greedy",
  "66-5": "Greedy",

  // 67: Spectre
  "67-1": "Farm-first",

  // 68: Ancient Apparition
  "68-4": "Greedy",
  "68-5": "Lane-protector",

  // 69: Doom
  "69-3": "Greedy",

  // 70: Ursa
  "70-1": "Aggressive",

  // 71: Spirit Breaker
  "71-4": "Roamer",

  // 72: Gyrocopter
  "72-1": "Fighting",
  "72-2": "Tempo",

  // 73: Alchemist
  "73-1": "Farm-first",
  "73-2": "Greedy",

  // 74: Invoker
  "74-2": "Tempo",

  // 75: Silencer
  "75-4": "Lane-dominator",
  "75-5": "Lane-protector",

  // 76: Outworld Destroyer
  "76-2": "Tempo",

  // 77: Lycan
  "77-1": "Split-push",
  "77-2": "Tempo",

  // 78: Brewmaster
  "78-3": "Initiator",

  // 79: Shadow Demon
  "79-4": "Roamer",
  "79-5": "Save",

  // 80: Lone Druid
  "80-1": "Split-push",

  // 81: Chaos Knight
  "81-1": "Fighting",

  // 82: Meepo
  "82-2": "Greedy",

  // 83: Treant Protector
  "83-4": "Roamer",
  "83-5": "Save",

  // 84: Ogre Magi
  "84-4": "Lane-dominator",
  "84-5": "Lane-protector",

  // 86: Rubick
  "86-4": "Roamer",
  "86-5": "Save",

  // 87: Disruptor
  "87-4": "Lane-dominator",
  "87-5": "Lane-protector",

  // 88: Nyx Assassin
  "88-4": "Roamer",

  // 89: Naga Siren
  "89-1": "Farm-first",

  // 90: Keeper of the Light
  "90-4": "Greedy",
  "90-5": "Lane-protector",

  // 91: Io
  "91-4": "Save",
  "91-5": "Save",

  // 92: Visage
  "92-2": "Tempo",
  "92-4": "Greedy",

  // 93: Slark
  "93-1": "Aggressive",

  // 94: Medusa
  "94-1": "Farm-first",
  "94-2": "Greedy",

  // 95: Troll Warlord
  "95-1": "Fighting",

  // 96: Centaur Warrunner
  "96-3": "Initiator",

  // 97: Magnus
  "97-2": "Tempo",
  "97-3": "Initiator",

  // 98: Timbersaw
  "98-3": "Frontline",

  // 99: Bristleback
  "99-3": "Frontline",

  // 100: Tusk
  "100-4": "Roamer",

  // 101: Skywrath Mage
  "101-4": "Lane-dominator",

  // 102: Abaddon
  "102-3": "Frontline",
  "102-5": "Save",

  // 103: Elder Titan
  "103-4": "Roamer",

  // 104: Legion Commander
  "104-3": "Initiator",

  // 106: Ember Spirit
  "106-2": "Tempo",

  // 107: Earth Spirit
  "107-4": "Roamer",

  // 108: Underlord
  "108-3": "Aura-carrier",

  // 109: Terrorblade
  "109-1": "Farm-first",

  // 110: Phoenix
  "110-3": "Frontline",
  "110-4": "Greedy",

  // 111: Oracle
  "111-5": "Save",

  // 112: Winter Wyvern
  "112-4": "Save",
  "112-5": "Save",

  // 113: Arc Warden
  "113-1": "Split-push",
  "113-2": "Greedy",

  // 114: Monkey King
  "114-1": "Fighting",
  "114-2": "Tempo",

  // 119: Dark Willow
  "119-4": "Roamer",

  // 120: Pangolier
  "120-3": "Initiator",

  // 121: Grimstroke
  "121-4": "Lane-dominator",
  "121-5": "Lane-protector",

  // 123: Hoodwink
  "123-4": "Roamer",

  // 126: Void Spirit
  "126-2": "Ganker",

  // 128: Snapfire
  "128-4": "Lane-dominator",
  "128-5": "Lane-protector",

  // 129: Mars
  "129-3": "Initiator",

  // 131: Ringmaster
  "131-4": "Roamer",

  // 135: Dawnbreaker
  "135-3": "Frontline",
  "135-5": "Save",

  // 136: Marci
  "136-3": "Initiator",
  "136-4": "Roamer",

  // 137: Primal Beast
  "137-3": "Initiator",

  // 138: Muerta
  "138-1": "Aggressive",
  "138-2": "Tempo",
};
