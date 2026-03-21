import { useState } from "react";
import LaneResultSelector from "./LaneResultSelector";
import DamageProfileInput from "./DamageProfileInput";
import EnemyItemTracker from "./EnemyItemTracker";
import ReEvaluateButton from "./ReEvaluateButton";

function GameStatePanel() {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="border-t border-bg-elevated pt-4 mt-4">
      {/* Collapsible header */}
      <button
        onClick={() => setIsExpanded((prev) => !prev)}
        className="flex items-center justify-between w-full group"
      >
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Game State
        </h2>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`text-gray-400 transition-transform duration-200 ${
            isExpanded ? "rotate-180" : ""
          }`}
        >
          <path d="M6 9L12 15L18 9" />
        </svg>
      </button>

      {/* Collapsible content */}
      <div
        className={`transition-all duration-300 ease-out overflow-hidden ${
          isExpanded ? "max-h-[600px]" : "max-h-0"
        }`}
      >
        {/* Lane Result */}
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5 mt-3">
          Lane Result
        </h3>
        <LaneResultSelector />

        {/* Damage Profile */}
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5 mt-3">
          Damage Profile
        </h3>
        <DamageProfileInput />

        {/* Enemy Items Spotted */}
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5 mt-3">
          Enemy Items Spotted
        </h3>
        <EnemyItemTracker />

        {/* Re-Evaluate CTA */}
        <div className="mt-4">
          <ReEvaluateButton />
        </div>
      </div>
    </div>
  );
}

export default GameStatePanel;
