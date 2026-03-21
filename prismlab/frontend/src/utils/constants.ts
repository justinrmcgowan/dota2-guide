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

// Mid-game adaptation constants

export const LANE_RESULT_OPTIONS = [
  { value: "won" as const, label: "Won", color: "text-radiant", bg: "bg-radiant/20", border: "border-radiant" },
  { value: "even" as const, label: "Even", color: "text-cyan-accent", bg: "bg-cyan-accent/20", border: "border-cyan-accent" },
  { value: "lost" as const, label: "Lost", color: "text-dire", bg: "bg-dire/20", border: "border-dire" },
] as const;

export const DAMAGE_PRESETS = [
  { label: "Heavy Physical", profile: { physical: 70, magical: 20, pure: 10 } },
  { label: "Heavy Magic", profile: { physical: 20, magical: 70, pure: 10 } },
  { label: "Mixed", profile: { physical: 40, magical: 40, pure: 20 } },
  { label: "Pure Burst", profile: { physical: 20, magical: 20, pure: 60 } },
] as const;

export const ENEMY_COUNTER_ITEMS = [
  { name: "bkb", label: "Black King Bar" },
  { name: "blink", label: "Blink Dagger" },
  { name: "force_staff", label: "Force Staff" },
  { name: "ghost", label: "Ghost Scepter" },
  { name: "sphere", label: "Linkens Sphere" },
  { name: "shivas_guard", label: "Shivas Guard" },
  { name: "blade_mail", label: "Blade Mail" },
  { name: "orchid", label: "Orchid Malevolence" },
  { name: "nullifier", label: "Nullifier" },
  { name: "heavens_halberd", label: "Heavens Halberd" },
  { name: "silver_edge", label: "Silver Edge" },
  { name: "aeon_disk", label: "Aeon Disk" },
  { name: "lotus_orb", label: "Lotus Orb" },
  { name: "assault", label: "Assault Cuirass" },
  { name: "pipe", label: "Pipe of Insight" },
] as const;
