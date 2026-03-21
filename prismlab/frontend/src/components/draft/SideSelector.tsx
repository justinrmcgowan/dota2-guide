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
        className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
          side === "radiant"
            ? "bg-radiant/20 text-radiant border-radiant"
            : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
        }`}
      >
        Radiant
      </button>
      <button
        role="radio"
        aria-checked={side === "dire"}
        onClick={() => setSide("dire")}
        className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
          side === "dire"
            ? "bg-dire/20 text-dire border-dire"
            : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
        }`}
      >
        Dire
      </button>
    </div>
  );
}

export default SideSelector;
