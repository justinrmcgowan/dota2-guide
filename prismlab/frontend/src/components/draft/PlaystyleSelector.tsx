import { useGameStore } from "../../stores/gameStore";
import { PLAYSTYLE_OPTIONS } from "../../utils/constants";

interface PlaystyleSelectorProps {
  role: number;
}

function PlaystyleSelector({ role }: PlaystyleSelectorProps) {
  const playstyle = useGameStore((s) => s.playstyle);
  const setPlaystyle = useGameStore((s) => s.setPlaystyle);

  const options = PLAYSTYLE_OPTIONS[role] ?? [];

  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const isActive = playstyle === opt;
        return (
          <button
            key={opt}
            onClick={() => setPlaystyle(opt)}
            className={`px-2 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              isActive
                ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
                : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

export default PlaystyleSelector;
