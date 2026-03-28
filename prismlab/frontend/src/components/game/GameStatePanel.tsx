import { useState } from "react";
import LaneResultSelector from "./LaneResultSelector";
import DamageProfileInput from "./DamageProfileInput";
import EnemyItemTracker from "./EnemyItemTracker";
import { useScreenshotStore } from "../../stores/screenshotStore";

function GameStatePanel() {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mt-6 pt-4">
      {/* Collapsible header */}
      <button
        onClick={() => setIsExpanded((prev) => !prev)}
        className="flex items-center justify-between w-full group"
      >
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider">
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
          className={`text-on-surface-variant transition-transform duration-200 ${
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
        <h3 className="text-xs font-medium text-on-surface-variant/70 uppercase tracking-wider mb-1.5 mt-3">
          Lane Result
        </h3>
        <LaneResultSelector />

        {/* Damage Profile */}
        <h3 className="text-xs font-medium text-on-surface-variant/70 uppercase tracking-wider mb-1.5 mt-3">
          Damage Profile
        </h3>
        <DamageProfileInput />

        {/* Enemy Items Spotted */}
        <h3 className="text-xs font-medium text-on-surface-variant/70 uppercase tracking-wider mb-1.5 mt-3">
          Enemy Items Spotted
        </h3>
        {/* Parse Screenshot button (per D-04) */}
        <button
          onClick={() => useScreenshotStore.getState().openModal("", "")}
          className="w-full mb-2 px-3 py-1.5 text-xs font-medium text-primary bg-primary-container/15 border border-outline-variant/15 hover:bg-primary-container/25 transition-colors flex items-center justify-center gap-1.5"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <path d="M21 15l-5-5L5 21"/>
          </svg>
          Parse Screenshot
        </button>
        <EnemyItemTracker />
      </div>
    </div>
  );
}

export default GameStatePanel;
