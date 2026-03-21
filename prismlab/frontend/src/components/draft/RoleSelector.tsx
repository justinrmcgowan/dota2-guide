import { useGameStore } from "../../stores/gameStore";
import { ROLE_OPTIONS } from "../../utils/constants";

function RoleSelector() {
  const role = useGameStore((s) => s.role);
  const setRole = useGameStore((s) => s.setRole);

  return (
    <div role="radiogroup" aria-label="Position" className="flex flex-wrap gap-1.5">
      {ROLE_OPTIONS.map((opt) => {
        const isActive = role === opt.value;
        return (
          <button
            key={opt.value}
            role="radio"
            aria-checked={isActive}
            onClick={() => setRole(opt.value)}
            className={`px-2 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              isActive
                ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
                : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export default RoleSelector;
