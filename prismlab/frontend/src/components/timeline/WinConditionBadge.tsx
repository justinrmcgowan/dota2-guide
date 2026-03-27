import type { WinConditionResponse } from "../../types/recommendation";

interface WinConditionBadgeProps {
  winCondition: WinConditionResponse;
}

const CONFIDENCE_OPACITY: Record<string, string> = {
  high: "opacity-100",
  medium: "opacity-75",
  low: "opacity-50",
};

// Capitalize first letter, preserve hyphens
function formatArchetype(archetype: string): string {
  return archetype.charAt(0).toUpperCase() + archetype.slice(1);
}

function WinConditionBadge({ winCondition }: WinConditionBadgeProps) {
  const alliedOpacity = CONFIDENCE_OPACITY[winCondition.allied_confidence] ?? "opacity-75";
  const enemyOpacity = winCondition.enemy_confidence
    ? (CONFIDENCE_OPACITY[winCondition.enemy_confidence] ?? "opacity-75")
    : "opacity-75";

  return (
    <div className="flex flex-wrap gap-2 mb-2 mt-1">
      {/* Allied archetype pill */}
      <span
        className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide font-display text-secondary ${alliedOpacity}`}
        title={`Allied strategy: ${winCondition.allied_archetype} (${winCondition.allied_confidence} confidence)`}
      >
        <span className="text-secondary">&#9650;</span>
        {formatArchetype(winCondition.allied_archetype)}
      </span>

      {/* Enemy archetype pill (only when classified) */}
      {winCondition.enemy_archetype && (
        <span
          className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide font-display text-dire ${enemyOpacity}`}
          title={`Enemy strategy: ${winCondition.enemy_archetype} (${winCondition.enemy_confidence ?? "low"} confidence)`}
        >
          <span className="text-dire">&#9660;</span>
          {formatArchetype(winCondition.enemy_archetype)}
        </span>
      )}
    </div>
  );
}

export default WinConditionBadge;
