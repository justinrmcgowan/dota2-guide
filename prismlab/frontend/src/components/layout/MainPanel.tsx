import { useGameStore } from "../../stores/gameStore";
import { useRecommendation } from "../../hooks/useRecommendation";
import { useRecommendationStore } from "../../stores/recommendationStore";
import { heroIconUrl, heroSlugFromInternal } from "../../utils/imageUrls";
import ItemTimeline from "../timeline/ItemTimeline";
import LoadingSkeleton from "../timeline/LoadingSkeleton";
import ErrorBanner from "../timeline/ErrorBanner";

function MainPanel() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const { data, isLoading, error, selectedItemId, selectItem, clear } =
    useRecommendation();
  const isPartial = useRecommendationStore((s) => s.isPartial);

  return (
    <main className="flex-1 bg-surface overflow-y-auto p-6">
      {/* Error banner at top (can coexist with timeline data) */}
      {error && (
        <ErrorBanner message={error} onDismiss={() => clear()} type="error" />
      )}

      {/* Fallback banner when AI reasoning unavailable */}
      {data?.fallback && !error && (
        <ErrorBanner
          message="AI reasoning unavailable"
          onDismiss={() => {}}
          type="fallback"
          fallbackReason={data.fallback_reason}
        />
      )}

      {/* Loading skeleton */}
      {isLoading && <LoadingSkeleton />}

      {/* Timeline with data */}
      {data && !isLoading && (
        <div>
          {/* Compact hero header */}
          {selectedHero && (
            <div className="flex items-center gap-2 mb-4">
              <img
                src={heroIconUrl(
                  heroSlugFromInternal(selectedHero.internal_name),
                )}
                alt={selectedHero.localized_name}
                className="w-8 h-8 rounded"
                loading="lazy"
              />
              <span className="text-on-surface font-semibold text-sm font-display">
                {selectedHero.localized_name}
              </span>
              <span className="text-on-surface-variant text-xs">Item Build</span>
            </div>
          )}

          <ItemTimeline
            data={data}
            selectedItemId={selectedItemId}
            onSelectItem={selectItem}
            isPartial={isPartial}
          />
        </div>
      )}

      {/* Empty states */}
      {!data && !isLoading && !error && (
        <div className="flex items-center justify-center h-full">
          <p className="text-on-surface-variant text-sm">
            {selectedHero
              ? "Select a hero and get your build"
              : "Select a hero from the sidebar to get started"}
          </p>
        </div>
      )}
    </main>
  );
}

export default MainPanel;
