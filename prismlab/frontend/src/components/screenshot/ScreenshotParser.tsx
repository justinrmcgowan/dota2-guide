import { useState, useEffect, useCallback, useRef } from "react";
import type { Hero } from "../../types/hero";
import { useScreenshotStore } from "../../stores/screenshotStore";
import { useGameStore } from "../../stores/gameStore";
import { useRefreshStore } from "../../stores/refreshStore";
import { useRecommendation } from "../../hooks/useRecommendation";
import { api } from "../../api/client";
import ParsedHeroRow from "./ParsedHeroRow";
import ItemEditPicker from "./ItemEditPicker";

interface ScreenshotParserProps {
  heroes: Hero[];
}

interface ItemInfo {
  name: string;
  internal_name: string;
}

function ScreenshotParser({ heroes }: ScreenshotParserProps) {
  const isOpen = useScreenshotStore((s) => s.isOpen);
  const imageData = useScreenshotStore((s) => s.imageData);
  const mimeType = useScreenshotStore((s) => s.mimeType);
  const parsedHeroes = useScreenshotStore((s) => s.parsedHeroes);
  const isLoading = useScreenshotStore((s) => s.isLoading);
  const error = useScreenshotStore((s) => s.error);
  const latencyMs = useScreenshotStore((s) => s.latencyMs);

  const [editingHeroIdx, setEditingHeroIdx] = useState<number | null>(null);
  const [allItems, setAllItems] = useState<ItemInfo[]>([]);

  const { recommend } = useRecommendation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const parseAttempted = useRef(false);

  // Fetch items list for the picker on modal open
  useEffect(() => {
    if (isOpen && allItems.length === 0) {
      fetch("/api/items")
        .then((r) => r.json())
        .then((data: Array<{ name: string; internal_name: string }>) => {
          setAllItems(
            data.map((item) => ({
              name: item.name,
              internal_name: item.internal_name,
            })),
          );
        })
        .catch(() => {
          // Items list is non-critical; picker will just be empty
        });
    }
  }, [isOpen, allItems.length]);

  // Auto-parse on open when imageData is present
  useEffect(() => {
    if (
      isOpen &&
      imageData &&
      imageData.length > 0 &&
      parsedHeroes.length === 0 &&
      !isLoading &&
      !parseAttempted.current
    ) {
      parseAttempted.current = true;
      const store = useScreenshotStore.getState();
      store.setLoading(true);
      store.setError(null);

      api
        .parseScreenshot({
          image_base64: imageData,
          media_type: mimeType ?? "image/png",
        })
        .then((response) => {
          store.setParsedHeroes(response.heroes);
          store.setLatency(response.latency_ms);
          if (response.error) {
            store.setError(response.error);
          }
        })
        .catch((err: Error) => {
          store.setError(err.message);
        })
        .finally(() => {
          store.setLoading(false);
        });
    }
  }, [isOpen, imageData, mimeType, parsedHeroes.length, isLoading]);

  // Reset parseAttempted ref when modal closes
  useEffect(() => {
    if (!isOpen) {
      parseAttempted.current = false;
    }
  }, [isOpen]);

  const handleApply = useCallback(() => {
    const gameStore = useGameStore.getState();
    const myHeroId = gameStore.selectedHero?.id ?? null;
    const mySide = gameStore.side ?? "radiant";

    // Split parsed heroes into allies and enemies using team field from vision parser.
    // If team field is available, use it directly. Otherwise fall back to finding
    // our hero in the list to determine sides.
    let allyHeroes: typeof parsedHeroes = [];
    let enemyHeroes: typeof parsedHeroes = [];

    const hasTeamData = parsedHeroes.some((h) => h.team !== null);

    if (hasTeamData) {
      // Vision parser provided team assignments — use them directly
      const myTeam = mySide === "dire" ? "dire" : "radiant";
      allyHeroes = parsedHeroes.filter(
        (h) => h.team === myTeam && h.hero_id !== myHeroId,
      );
      enemyHeroes = parsedHeroes.filter((h) => h.team !== myTeam);
    } else if (myHeroId && parsedHeroes.length >= 6) {
      // Fallback: use hero position in list (Radiant first 5, Dire last 5)
      const myIdx = parsedHeroes.findIndex((h) => h.hero_id === myHeroId);
      if (myIdx >= 0 && myIdx < 5) {
        allyHeroes = parsedHeroes.slice(0, 5).filter((h) => h.hero_id !== myHeroId);
        enemyHeroes = parsedHeroes.slice(5, 10);
      } else if (myIdx >= 5) {
        enemyHeroes = parsedHeroes.slice(0, 5);
        allyHeroes = parsedHeroes.slice(5, 10).filter((h) => h.hero_id !== myHeroId);
      } else {
        enemyHeroes = parsedHeroes.slice(0, 5);
      }
    } else {
      enemyHeroes = parsedHeroes.slice(0, 5);
    }

    // Set allies (up to 4, excluding self)
    allyHeroes.slice(0, 4).forEach((parsedHero, idx) => {
      const matched = heroes.find((h) => h.id === parsedHero.hero_id);
      if (matched) {
        gameStore.setAlly(idx, matched);
      }
    });

    // Set opponents (up to 5)
    enemyHeroes.slice(0, 5).forEach((parsedHero, idx) => {
      const matched = heroes.find((h) => h.id === parsedHero.hero_id);
      if (matched) {
        gameStore.setOpponent(idx, matched);
      }
    });

    // Set enemy items -- collect from ENEMY heroes only
    const itemNames = enemyHeroes.flatMap((h) =>
      h.items.map((i) => i.internal_name),
    );
    const uniqueItems = [...new Set(itemNames)];
    gameStore.setEnemyItemsSpotted(uniqueItems);

    // Collect enemy KDA/level context from enemy heroes only
    const enemyCtx = enemyHeroes
      .filter((h) => h.hero_id !== null)
      .map((h) => ({
        hero_id: h.hero_id!,
        kills: h.kills,
        deaths: h.deaths,
        assists: h.assists,
        level: h.level,
      }));
    gameStore.setEnemyContext(enemyCtx);

    // Show toast
    useRefreshStore
      .getState()
      .showToast("Enemy builds applied -- updating recommendations.");

    // Trigger recommendation refresh
    recommend();

    // Close modal
    useScreenshotStore.getState().closeModal();
  }, [parsedHeroes, heroes, recommend]);

  const handleRetry = useCallback(() => {
    if (!imageData || imageData.length === 0) return;
    const store = useScreenshotStore.getState();
    store.setLoading(true);
    store.setError(null);
    store.setParsedHeroes([]);

    api
      .parseScreenshot({
        image_base64: imageData,
        media_type: mimeType ?? "image/png",
      })
      .then((response) => {
        store.setParsedHeroes(response.heroes);
        store.setLatency(response.latency_ms);
        if (response.error) {
          store.setError(response.error);
        }
      })
      .catch((err: Error) => {
        store.setError(err.message);
      })
      .finally(() => {
        store.setLoading(false);
      });
  }, [imageData, mimeType]);

  // File/drag-drop handling for upload zone
  const handleFileUpload = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const commaIdx = dataUrl.indexOf(",");
      if (commaIdx === -1) return;

      const header = dataUrl.slice(0, commaIdx);
      const base64 = dataUrl.slice(commaIdx + 1);
      const mimeMatch = header.match(/data:(.*?);/);
      const detectedMime = mimeMatch?.[1] ?? "image/png";

      useScreenshotStore.getState().openModal(base64, detectedMime);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const file = e.dataTransfer.files[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload],
  );

  if (!isOpen) return null;

  const hasImage = imageData && imageData.length > 0;
  const showUploadZone = !hasImage;
  const parseComplete = !isLoading && parsedHeroes.length > 0;
  const parseEmpty =
    !isLoading && !error && parsedHeroes.length === 0 && hasImage && !isLoading;

  return (
    <>
      {/* Backdrop — blood-glass (D-17) */}
      <div
        className="fixed inset-0 bg-primary-container/30 backdrop-blur-md z-40"
        onClick={() => useScreenshotStore.getState().closeModal()}
      />

      {/* Modal container */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="max-w-3xl w-full bg-surface-container-highest shadow-glow max-h-[85vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header — No-Line Rule: removed border-b */}
          <div className="flex items-center justify-between px-5 py-4">
            <h2 className="text-lg font-bold text-secondary font-display">
              Screenshot Parser
            </h2>
            <button
              onClick={() => useScreenshotStore.getState().closeModal()}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label="Close"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 6L6 18" />
                <path d="M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="px-5 py-4 space-y-4">
            {/* Upload zone (when no image) */}
            {showUploadZone && (
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-outline-variant p-8 text-center cursor-pointer hover:border-primary transition-colors"
              >
                <svg
                  className="mx-auto mb-3 text-on-surface-variant"
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path d="M21 15l-5-5L5 21" />
                </svg>
                <p className="text-on-surface-variant text-sm">
                  Drag & drop a screenshot here, or click to browse
                </p>
                <p className="text-on-surface-variant/50 text-xs mt-1">
                  Supports PNG, JPG, WebP
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </div>
            )}

            {/* Screenshot thumbnail */}
            {hasImage && (
              <div className="flex justify-center">
                <img
                  src={`data:${mimeType};base64,${imageData}`}
                  alt="Pasted screenshot"
                  className="max-h-48 object-contain"
                />
              </div>
            )}

            {/* Loading state */}
            {isLoading && (
              <div className="flex flex-col items-center py-6 gap-3">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-on-surface-variant">
                  Analyzing scoreboard...
                </p>
              </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
              <div className="bg-dire/10 border border-dire/30 px-4 py-3 space-y-2">
                <p className="text-sm text-dire">{error}</p>
                <button
                  onClick={handleRetry}
                  className="text-xs text-primary hover:text-primary/80 underline"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Parse empty result */}
            {parseEmpty && parseAttempted.current && (
              <div className="text-center py-4">
                <p className="text-sm text-on-surface-variant">
                  No heroes detected in screenshot
                </p>
              </div>
            )}

            {/* Parsed hero rows */}
            {parseComplete && (
              <div className="space-y-2">
                {parsedHeroes.map((hero, idx) => (
                  <div key={`hero-${idx}`} className="relative">
                    <ParsedHeroRow
                      hero={hero}
                      heroIdx={idx}
                      onAddItem={(hIdx) => setEditingHeroIdx(hIdx)}
                    />
                    {/* Item edit picker positioned below hero row */}
                    {editingHeroIdx === idx && (
                      <ItemEditPicker
                        heroIdx={idx}
                        onClose={() => setEditingHeroIdx(null)}
                        items={allItems}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Latency indicator */}
            {latencyMs !== null && !isLoading && (
              <p className="text-xs text-on-surface-variant/50 text-right">
                Parsed in {latencyMs}ms
              </p>
            )}
          </div>

          {/* Footer — No-Line Rule: removed border-t */}
          <div className="flex items-center justify-between px-5 py-4">
            <button
              onClick={() => useScreenshotStore.getState().closeModal()}
              className="px-4 py-2 text-sm text-on-surface-variant hover:text-on-surface bg-surface-container-high transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={parsedHeroes.length === 0 || isLoading}
              className="px-4 py-2 text-sm font-medium text-on-surface bg-primary-container hover:outline hover:outline-1 hover:outline-[#AA8986] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Apply to Build
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default ScreenshotParser;
