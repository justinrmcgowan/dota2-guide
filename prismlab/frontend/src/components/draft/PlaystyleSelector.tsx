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
            className={`px-2 py-1.5 text-xs font-medium border transition-colors ${
              isActive
                ? "bg-primary-container/20 text-primary border-primary/40"
                : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
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
