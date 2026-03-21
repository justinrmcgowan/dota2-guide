export const ATTR_COLORS: Record<string, string> = {
  str: "text-attr-str",
  agi: "text-attr-agi",
  int: "text-attr-int",
  all: "text-attr-all",
};

export const ATTR_BG_COLORS: Record<string, string> = {
  str: "bg-attr-str",
  agi: "bg-attr-agi",
  int: "bg-attr-int",
  all: "bg-attr-all",
};

export const ROLE_OPTIONS = [
  { value: 1, label: "Pos 1 Carry" },
  { value: 2, label: "Pos 2 Mid" },
  { value: 3, label: "Pos 3 Off" },
  { value: 4, label: "Pos 4 Soft Sup" },
  { value: 5, label: "Pos 5 Hard Sup" },
] as const;

export const PLAYSTYLE_OPTIONS: Record<number, string[]> = {
  1: ["Farm-first", "Aggressive", "Split-push", "Fighting"],
  2: ["Tempo", "Ganker", "Greedy", "Space-maker"],
  3: ["Frontline", "Aura-carrier", "Initiator", "Greedy"],
  4: ["Roamer", "Lane-dominator", "Greedy", "Save"],
  5: ["Lane-protector", "Roamer", "Greedy", "Save"],
};

export const LANE_OPTIONS = [
  { value: "safe" as const, label: "Safe" },
  { value: "mid" as const, label: "Mid" },
  { value: "off" as const, label: "Off" },
] as const;
