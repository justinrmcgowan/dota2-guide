import { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "../api/client";
import { itemImageUrl } from "../utils/imageUrls";
import type {
  MatchHistoryItem,
  MatchHistoryResponse,
  MatchStatsResponse,
} from "../types/matchLog";

/* ------------------------------------------------------------------ */
/* Constants                                                          */
/* ------------------------------------------------------------------ */

const PAGE_SIZE = 20;

const ROLE_LABELS: Record<number, string> = {
  1: "Pos 1",
  2: "Pos 2",
  3: "Pos 3",
  4: "Pos 4",
  5: "Pos 5",
};

const PHASE_ORDER = ["starting", "early", "core", "mid", "late", "luxury", "situational"];

type SortKey =
  | "played_at"
  | "hero_name"
  | "role"
  | "win"
  | "duration_seconds"
  | "kda"
  | "gpm"
  | "follow_rate"
  | "engine_mode";
type SortDir = "asc" | "desc";

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "--";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatRelativeDate(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "--";
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD}d ago`;
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function followRateColor(rate: number | null): string {
  if (rate == null) return "text-on-surface-variant";
  const pct = rate * 100;
  if (pct >= 70) return "text-radiant";
  if (pct >= 40) return "text-yellow-400";
  return "text-dire";
}

function pctDisplay(value: number | null): string {
  if (value == null) return "--";
  return `${Math.round(value * 100)}%`;
}

/* ------------------------------------------------------------------ */
/* Sorting                                                            */
/* ------------------------------------------------------------------ */

function sortMatches(
  matches: MatchHistoryItem[],
  key: SortKey,
  dir: SortDir,
): MatchHistoryItem[] {
  const sorted = [...matches];
  const mul = dir === "asc" ? 1 : -1;

  sorted.sort((a, b) => {
    let cmp = 0;
    switch (key) {
      case "played_at":
        cmp = a.played_at.localeCompare(b.played_at);
        break;
      case "hero_name":
        cmp = a.hero_name.localeCompare(b.hero_name);
        break;
      case "role":
        cmp = a.role - b.role;
        break;
      case "win":
        cmp = (a.win ? 1 : 0) - (b.win ? 1 : 0);
        break;
      case "duration_seconds":
        cmp = (a.duration_seconds ?? 0) - (b.duration_seconds ?? 0);
        break;
      case "kda":
        cmp = (a.kills + a.assists) / Math.max(a.deaths, 1) -
              (b.kills + b.assists) / Math.max(b.deaths, 1);
        break;
      case "gpm":
        cmp = a.gpm - b.gpm;
        break;
      case "follow_rate":
        cmp = (a.follow_rate ?? -1) - (b.follow_rate ?? -1);
        break;
      case "engine_mode":
        cmp = (a.engine_mode ?? "").localeCompare(b.engine_mode ?? "");
        break;
    }
    return cmp * mul;
  });

  return sorted;
}

/* ------------------------------------------------------------------ */
/* Sub-components (local)                                             */
/* ------------------------------------------------------------------ */

function StatCard({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: string;
  colorClass?: string;
}) {
  return (
    <div className="bg-surface-container rounded-lg px-4 py-3 flex flex-col items-center min-w-[120px]">
      <span className="text-xs text-on-surface-variant uppercase tracking-wider">
        {label}
      </span>
      <span className={`text-xl font-display font-bold mt-1 ${colorClass ?? "text-secondary"}`}>
        {value}
      </span>
    </div>
  );
}

function SortHeader({
  label,
  sortKey: columnKey,
  currentKey,
  currentDir,
  onSort,
  className,
}: {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey;
  currentDir: SortDir;
  onSort: (key: SortKey) => void;
  className?: string;
}) {
  const isActive = currentKey === columnKey;
  const arrow = isActive ? (currentDir === "asc" ? " \u25B2" : " \u25BC") : "";
  return (
    <th
      className={`px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-primary transition-colors ${
        isActive ? "text-primary" : "text-on-surface-variant"
      } ${className ?? ""}`}
      onClick={() => onSort(columnKey)}
    >
      {label}
      {arrow}
    </th>
  );
}

function MatchDetail({ match }: { match: MatchHistoryItem }) {
  // Group items by slot type: inventory first, then backpack, then neutral
  const inventory = match.items.filter((i) => i.slot_type === "inventory");
  const backpack = match.items.filter((i) => i.slot_type === "backpack");
  const neutral = match.items.filter((i) => i.slot_type === "neutral");

  // Group recommendations by phase
  const recsByPhase: Record<string, typeof match.recommendations> = {};
  for (const rec of match.recommendations) {
    (recsByPhase[rec.phase] ??= []).push(rec);
  }
  const sortedPhases = Object.keys(recsByPhase).sort(
    (a, b) => PHASE_ORDER.indexOf(a) - PHASE_ORDER.indexOf(b),
  );

  return (
    <td colSpan={9} className="px-4 py-4 bg-surface-container-lowest">
      <div className="space-y-4">
        {/* Item Build */}
        {match.items.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
              Item Build
            </h4>
            <div className="flex items-center gap-1 flex-wrap">
              {inventory.map((item, i) => (
                <img
                  key={`inv-${i}`}
                  src={itemImageUrl(item.item_name)}
                  alt={item.item_name}
                  title={item.item_name.replace(/_/g, " ")}
                  className="w-9 h-7 rounded border border-outline-variant object-cover"
                />
              ))}
              {backpack.length > 0 && (
                <>
                  <span className="text-on-surface-variant text-xs mx-1">|</span>
                  {backpack.map((item, i) => (
                    <img
                      key={`bp-${i}`}
                      src={itemImageUrl(item.item_name)}
                      alt={item.item_name}
                      title={`Backpack: ${item.item_name.replace(/_/g, " ")}`}
                      className="w-9 h-7 rounded border border-outline-variant object-cover opacity-60"
                    />
                  ))}
                </>
              )}
              {neutral.length > 0 && (
                <>
                  <span className="text-on-surface-variant text-xs mx-1">|</span>
                  {neutral.map((item, i) => (
                    <img
                      key={`nt-${i}`}
                      src={itemImageUrl(item.item_name)}
                      alt={item.item_name}
                      title={`Neutral: ${item.item_name.replace(/_/g, " ")}`}
                      className="w-9 h-7 rounded border border-yellow-700/50 object-cover"
                    />
                  ))}
                </>
              )}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {sortedPhases.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
              Recommendations
            </h4>
            <div className="space-y-2">
              {sortedPhases.map((phase) => (
                <div key={phase}>
                  <span className="text-xs text-secondary capitalize font-semibold">
                    {phase}
                  </span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {recsByPhase[phase].map((rec, i) => (
                      <div
                        key={`${phase}-${i}`}
                        className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs ${
                          rec.was_purchased
                            ? "bg-radiant/10 text-radiant"
                            : "bg-surface-container text-on-surface-variant"
                        }`}
                      >
                        <img
                          src={itemImageUrl(rec.item_name)}
                          alt={rec.item_name}
                          className="w-6 h-5 rounded object-cover"
                        />
                        <span>{rec.item_name.replace(/_/g, " ")}</span>
                        <span
                          className={`text-[10px] px-1 rounded ${
                            rec.priority === "core"
                              ? "bg-primary/20 text-primary"
                              : rec.priority === "luxury"
                                ? "bg-secondary/20 text-secondary"
                                : "bg-surface-container-high text-on-surface-variant"
                          }`}
                        >
                          {rec.priority}
                        </span>
                        <span>
                          {rec.was_purchased ? (
                            <svg className="w-3.5 h-3.5 text-radiant" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="w-3.5 h-3.5 text-dire" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Overall Strategy */}
        {match.overall_strategy && (
          <div>
            <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-1">
              Strategy
            </h4>
            <p className="text-sm text-on-surface-variant italic leading-relaxed">
              {match.overall_strategy}
            </p>
          </div>
        )}
      </div>
    </td>
  );
}

/* ------------------------------------------------------------------ */
/* Main Component                                                     */
/* ------------------------------------------------------------------ */

interface MatchHistoryProps {
  onBack: () => void;
}

export default function MatchHistory({ onBack }: MatchHistoryProps) {
  /* --- data state --- */
  const [stats, setStats] = useState<MatchStatsResponse | null>(null);
  const [data, setData] = useState<MatchHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* --- filter state --- */
  const [heroFilter, setHeroFilter] = useState("");
  const [resultFilter, setResultFilter] = useState<"" | "win" | "loss">("");
  const [modeFilter, setModeFilter] = useState<"" | "fast" | "auto" | "deep">("");

  /* --- table state --- */
  const [sortKey, setSortKey] = useState<SortKey>("played_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [page, setPage] = useState(0);

  /* --- fetch data --- */
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Parameters<typeof api.getMatchHistory>[0] = {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      };
      if (resultFilter) params.result = resultFilter;
      if (modeFilter) params.mode = modeFilter;

      const [historyRes, statsRes] = await Promise.all([
        api.getMatchHistory(params),
        page === 0 ? api.getMatchStats() : Promise.resolve(null),
      ]);

      setData(historyRes);
      if (statsRes) setStats(statsRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load match history");
    } finally {
      setLoading(false);
    }
  }, [page, resultFilter, modeFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Reset page when filters change
  useEffect(() => {
    setPage(0);
    setExpandedId(null);
  }, [resultFilter, modeFilter, heroFilter]);

  /* --- derived data --- */
  const filteredMatches = useMemo(() => {
    if (!data) return [];
    let matches = data.matches;
    // Client-side hero name filter (server uses hero_id which requires lookup)
    if (heroFilter.trim()) {
      const q = heroFilter.toLowerCase();
      matches = matches.filter((m) =>
        m.hero_name.toLowerCase().includes(q),
      );
    }
    return sortMatches(matches, sortKey, sortDir);
  }, [data, heroFilter, sortKey, sortDir]);

  const totalMatches = data?.total ?? 0;
  const startIdx = page * PAGE_SIZE + 1;
  const endIdx = Math.min((page + 1) * PAGE_SIZE, totalMatches);

  /* --- sort handler --- */
  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  /* --- render --- */
  return (
    <div className="flex-1 overflow-y-auto px-6 py-5 relative z-10">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-2xl font-display font-bold text-on-surface">
          Match History
        </h2>
        <button
          onClick={onBack}
          className="text-sm text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1"
        >
          <span>&larr;</span> Back to Advisor
        </button>
      </div>

      {/* Aggregate Stats */}
      {stats && (
        <div className="flex flex-wrap gap-3 mb-5">
          <StatCard label="Total Games" value={String(stats.total_games)} />
          <StatCard
            label="Win Rate"
            value={pctDisplay(stats.win_rate)}
            colorClass={stats.win_rate >= 0.5 ? "text-radiant" : "text-dire"}
          />
          <StatCard
            label="Avg Follow Rate"
            value={pctDisplay(stats.avg_follow_rate)}
            colorClass={followRateColor(stats.avg_follow_rate)}
          />
          <StatCard
            label="Follow Rate (Wins)"
            value={pctDisplay(stats.avg_follow_rate_wins)}
            colorClass={followRateColor(stats.avg_follow_rate_wins)}
          />
          <StatCard
            label="Follow Rate (Losses)"
            value={pctDisplay(stats.avg_follow_rate_losses)}
            colorClass={followRateColor(stats.avg_follow_rate_losses)}
          />
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter by hero..."
          value={heroFilter}
          onChange={(e) => setHeroFilter(e.target.value)}
          className="bg-surface-container border border-outline-variant rounded px-3 py-1.5 text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary w-48"
        />
        <select
          value={resultFilter}
          onChange={(e) => setResultFilter(e.target.value as typeof resultFilter)}
          className="bg-surface-container border border-outline-variant rounded px-3 py-1.5 text-sm text-on-surface focus:outline-none focus:border-primary"
        >
          <option value="">All Results</option>
          <option value="win">Wins</option>
          <option value="loss">Losses</option>
        </select>
        <select
          value={modeFilter}
          onChange={(e) => setModeFilter(e.target.value as typeof modeFilter)}
          className="bg-surface-container border border-outline-variant rounded px-3 py-1.5 text-sm text-on-surface focus:outline-none focus:border-primary"
        >
          <option value="">All Modes</option>
          <option value="fast">Fast</option>
          <option value="auto">Auto</option>
          <option value="deep">Deep</option>
        </select>
      </div>

      {/* Loading / Error / Empty States */}
      {loading && (
        <div className="text-center text-on-surface-variant py-12">
          Loading match history...
        </div>
      )}

      {error && (
        <div className="text-center text-dire py-12">
          {error}
        </div>
      )}

      {!loading && !error && filteredMatches.length === 0 && (
        <div className="text-center text-on-surface-variant py-16">
          <p className="text-lg mb-2">No matches logged yet.</p>
          <p className="text-sm">
            Play a game with GSI connected and your match data will appear here.
          </p>
        </div>
      )}

      {/* Match Table */}
      {!loading && !error && filteredMatches.length > 0 && (
        <>
          <div className="rounded-lg border border-outline-variant overflow-hidden">
            <table className="w-full">
              <thead className="bg-surface-container-low">
                <tr>
                  <SortHeader label="Date" sortKey="played_at" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortHeader label="Hero" sortKey="hero_name" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} />
                  <SortHeader label="Role" sortKey="role" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-20" />
                  <SortHeader label="Result" sortKey="win" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-20" />
                  <SortHeader label="Duration" sortKey="duration_seconds" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-24" />
                  <SortHeader label="KDA" sortKey="kda" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-24" />
                  <SortHeader label="GPM" sortKey="gpm" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-20" />
                  <SortHeader label="Follow %" sortKey="follow_rate" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-24" />
                  <SortHeader label="Mode" sortKey="engine_mode" currentKey={sortKey} currentDir={sortDir} onSort={handleSort} className="w-20" />
                </tr>
              </thead>
              <tbody>
                {filteredMatches.map((match, idx) => (
                  <MatchRow
                    key={match.id}
                    match={match}
                    index={idx}
                    expanded={expandedId === match.id}
                    onToggle={() =>
                      setExpandedId(expandedId === match.id ? null : match.id)
                    }
                  />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4 text-sm text-on-surface-variant">
            <span>
              Showing {startIdx}--{endIdx} of {totalMatches} matches
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="px-3 py-1 rounded border border-outline-variant hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                disabled={endIdx >= totalMatches}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-outline-variant hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* MatchRow (extracted for readability)                                */
/* ------------------------------------------------------------------ */

function MatchRow({
  match,
  index,
  expanded,
  onToggle,
}: {
  match: MatchHistoryItem;
  index: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  const bgClass = index % 2 === 0 ? "bg-surface" : "bg-surface-container-lowest";

  return (
    <>
      <tr
        className={`${bgClass} hover:bg-surface-container-high cursor-pointer transition-colors`}
        onClick={onToggle}
      >
        <td className="px-3 py-2 text-sm text-on-surface-variant whitespace-nowrap">
          {formatRelativeDate(match.played_at)}
        </td>
        <td className="px-3 py-2 text-sm text-on-surface font-medium">
          {match.hero_name}
        </td>
        <td className="px-3 py-2 text-sm text-on-surface-variant">
          {ROLE_LABELS[match.role] ?? `Pos ${match.role}`}
        </td>
        <td className="px-3 py-2">
          <span
            className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
              match.win
                ? "bg-radiant/15 text-radiant"
                : "bg-dire/15 text-dire"
            }`}
          >
            {match.win ? "W" : "L"}
          </span>
        </td>
        <td className="px-3 py-2 text-sm text-on-surface-variant tabular-nums">
          {formatDuration(match.duration_seconds)}
        </td>
        <td className="px-3 py-2 text-sm text-on-surface tabular-nums">
          {match.kills}/{match.deaths}/{match.assists}
        </td>
        <td className="px-3 py-2 text-sm text-on-surface-variant tabular-nums">
          {match.gpm}
        </td>
        <td className={`px-3 py-2 text-sm font-semibold tabular-nums ${followRateColor(match.follow_rate)}`}>
          {pctDisplay(match.follow_rate)}
        </td>
        <td className="px-3 py-2 text-sm text-on-surface-variant capitalize">
          {match.engine_mode ?? "--"}
        </td>
      </tr>
      {expanded && (
        <tr>
          <MatchDetail match={match} />
        </tr>
      )}
    </>
  );
}
