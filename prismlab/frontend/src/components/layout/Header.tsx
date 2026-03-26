import { useState, useEffect } from "react";
import { api, type DataFreshness } from "../../api/client";
import GsiStatusIndicator from "./GsiStatusIndicator";
import GameClock from "../clock/GameClock";

function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diffMs = now - then;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 1) return "just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

interface HeaderProps {
  onOpenSettings?: () => void;
}

function Header({ onOpenSettings }: HeaderProps) {
  const [freshness, setFreshness] = useState<DataFreshness | null>(null);

  useEffect(() => {
    api.getDataFreshness().then(setFreshness).catch(() => {
      // Silently ignore fetch failures -- header renders fine without freshness data
    });
  }, []);

  const freshnessLabel = freshness?.last_refresh
    ? `Data: ${formatRelativeTime(freshness.last_refresh)}`
    : freshness
      ? "Data: seeded"
      : null;

  const freshnessTitle = freshness?.last_refresh
    ? `Last refresh: ${freshness.last_refresh}`
    : freshness
      ? "Data from initial seed only"
      : undefined;

  return (
    <header className="h-14 bg-bg-secondary border-b border-bg-elevated px-4 flex items-center shrink-0">
      <div className="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 32 32"
          className="w-7 h-7"
        >
          <defs>
            <linearGradient id="header-prism" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00d4ff" />
              <stop offset="50%" stopColor="#6aff97" />
              <stop offset="100%" stopColor="#00d4ff" />
            </linearGradient>
          </defs>
          <path
            d="M16 2 L28 26 L4 26 Z"
            fill="none"
            stroke="url(#header-prism)"
            strokeWidth="2"
          />
          <path
            d="M16 8 L22 22 L10 22 Z"
            fill="url(#header-prism)"
            opacity="0.3"
          />
        </svg>
        <h1 className="text-cyan-accent font-bold text-xl font-body">
          Prismlab
        </h1>
      </div>

      <div className="ml-4">
        <GsiStatusIndicator />
      </div>

      <div className="ml-2">
        <GameClock />
      </div>

      <div className="ml-auto flex items-center gap-3">
        {freshnessLabel && (
          <span
            className="text-xs text-text-muted"
            title={freshnessTitle}
          >
            {freshnessLabel}
          </span>
        )}
        {onOpenSettings && (
          <button
            onClick={onOpenSettings}
            className="text-text-muted hover:text-cyan-accent transition-colors"
            title="Settings"
            aria-label="Open settings"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5"
            >
              <path
                fillRule="evenodd"
                d="M11.078 2.25c-.917 0-1.699.663-1.85 1.567L9.05 4.889c-.02.12-.115.26-.297.348a7.493 7.493 0 00-.986.57c-.166.115-.334.126-.45.083L6.3 5.508a1.875 1.875 0 00-2.282.819l-.922 1.597a1.875 1.875 0 00.432 2.385l.84.692c.095.078.17.229.154.43a7.598 7.598 0 000 1.139c.015.2-.059.352-.153.43l-.841.692a1.875 1.875 0 00-.432 2.385l.922 1.597a1.875 1.875 0 002.282.818l1.019-.382c.115-.043.283-.031.45.082.312.214.641.405.985.57.182.088.277.228.297.35l.178 1.071c.151.904.933 1.567 1.85 1.567h1.844c.916 0 1.699-.663 1.85-1.567l.178-1.072c.02-.12.114-.26.297-.349.344-.165.673-.356.985-.57.167-.114.335-.125.45-.082l1.02.382a1.875 1.875 0 002.28-.819l.923-1.597a1.875 1.875 0 00-.432-2.385l-.84-.692c-.095-.078-.17-.229-.154-.43a7.614 7.614 0 000-1.139c-.016-.2.059-.352.153-.43l.84-.692c.708-.582.891-1.59.433-2.385l-.922-1.597a1.875 1.875 0 00-2.282-.818l-1.02.382c-.114.043-.282.031-.449-.083a7.49 7.49 0 00-.985-.57c-.183-.087-.277-.227-.297-.348l-.179-1.072a1.875 1.875 0 00-1.85-1.567h-1.843zM12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;
