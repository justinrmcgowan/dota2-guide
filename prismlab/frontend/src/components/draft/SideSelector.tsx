import { useGameStore } from "../../stores/gameStore";

function SideSelector() {
  const side = useGameStore((s) => s.side);
  const setSide = useGameStore((s) => s.setSide);

  return (
    <div role="radiogroup" aria-label="Side" className="flex gap-2">
      <button
        role="radio"
        aria-checked={side === "radiant"}
        onClick={() => setSide("radiant")}
        className={`flex-1 py-1.5 text-xs font-medium border transition-colors ${
          side === "radiant"
            ? "bg-radiant/20 text-radiant border-radiant"
            : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
        }`}
      >
        Radiant
      </button>
      <button
        role="radio"
        aria-checked={side === "dire"}
        onClick={() => setSide("dire")}
        className={`flex-1 py-1.5 text-xs font-medium border transition-colors ${
          side === "dire"
            ? "bg-dire/20 text-dire border-dire"
            : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
        }`}
      >
        Dire
      </button>
    </div>
  );
}

export default SideSelector;
