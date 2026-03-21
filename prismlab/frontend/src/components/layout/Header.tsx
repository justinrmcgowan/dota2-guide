import { useState, useEffect } from "react";
import { api, type DataFreshness } from "../../api/client";

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

function Header() {
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
      {freshnessLabel && (
        <span
          className="ml-auto text-xs text-text-muted"
          title={freshnessTitle}
        >
          {freshnessLabel}
        </span>
      )}
    </header>
  );
}

export default Header;
