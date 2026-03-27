import { useState, useEffect, useRef, useMemo } from "react";
import { useHeroes } from "../../hooks/useHeroes";
import { createHeroSearcher, searchHeroes } from "../../utils/heroSearch";
import HeroPortrait from "./HeroPortrait";
import type { Hero } from "../../types/hero";

interface HeroPickerProps {
  value: Hero | null;
  onSelect: (hero: Hero) => void;
  onClear: () => void;
  excludedHeroIds?: Set<number>;
  placeholder?: string;
  compact?: boolean;
}

function HeroPicker({
  value,
  onSelect,
  onClear,
  excludedHeroIds = new Set(),
  placeholder = "Search heroes...",
  compact = false,
}: HeroPickerProps) {
  const { heroes, loading, error } = useHeroes();

  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const searcher = useMemo(() => {
    if (heroes.length === 0) return null;
    return createHeroSearcher(heroes);
  }, [heroes]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, []);

  const searchLimit = compact ? 8 : 10;
  const browseLimit = compact ? 8 : 20;

  // Build results list
  const results = useMemo(() => {
    if (!searcher) return [];

    let matched: Hero[];
    if (query.trim()) {
      matched = searchHeroes(searcher, query).slice(0, searchLimit);
    } else if (isOpen) {
      // Show all heroes sorted alphabetically when dropdown is open with no query
      matched = [...heroes]
        .sort((a, b) => a.localized_name.localeCompare(b.localized_name))
        .slice(0, browseLimit);
    } else {
      return [];
    }

    // Sort: non-excluded first, then excluded, each group sorted by name
    const nonExcluded = matched
      .filter((h) => !excludedHeroIds.has(h.id))
      .sort((a, b) => a.localized_name.localeCompare(b.localized_name));
    const excluded = matched
      .filter((h) => excludedHeroIds.has(h.id))
      .sort((a, b) => a.localized_name.localeCompare(b.localized_name));

    return [...nonExcluded, ...excluded];
  }, [searcher, query, isOpen, heroes, excludedHeroIds, searchLimit, browseLimit]);

  function handleSelect(hero: Hero) {
    onSelect(hero);
    setQuery("");
    setIsOpen(false);
  }

  function handleClear() {
    onClear();
    setQuery("");
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  }

  if (loading) {
    return <p className="text-on-surface-variant text-sm">Loading heroes...</p>;
  }

  if (error) {
    return <p className="text-dire text-sm">Error: {error}</p>;
  }

  // Selected hero display
  if (value) {
    return (
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <HeroPortrait hero={value} size="lg" selected />
        </div>
        <button
          onClick={handleClear}
          className="text-on-surface-variant hover:text-on-surface transition-colors p-1 shrink-0"
          aria-label="Clear hero selection"
          title="Clear selection"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-5 h-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    );
  }

  // Search input and dropdown
  const inputTextSize = compact ? "text-xs" : "text-sm";

  return (
    <div ref={containerRef} className="relative" onKeyDown={handleKeyDown}>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
        className={`w-full bg-surface-container-lowest border-b border-outline-variant/15 text-on-surface placeholder-on-surface-variant/40 px-3 py-2 ${inputTextSize} focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent`}
      />

      {isOpen && results.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1 max-h-64 overflow-y-auto bg-surface-container-low shadow-lg z-10">
          {results.map((hero) => {
            const isExcluded = excludedHeroIds.has(hero.id);
            return (
              <div
                key={hero.id}
                className={
                  isExcluded
                    ? "opacity-40 cursor-not-allowed"
                    : "hover:bg-surface-container-high"
                }
              >
                <HeroPortrait
                  hero={hero}
                  size="sm"
                  onClick={isExcluded ? undefined : () => handleSelect(hero)}
                  disabled={isExcluded}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default HeroPicker;
