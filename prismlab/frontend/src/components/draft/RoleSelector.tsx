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
            className={`px-2 py-1.5 text-xs font-medium border transition-colors ${
              isActive
                ? "bg-primary-container/20 text-primary border-primary/40"
                : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
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
