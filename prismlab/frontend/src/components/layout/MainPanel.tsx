import { useGameStore } from "../../stores/gameStore";
import { useRecommendation } from "../../hooks/useRecommendation";
import { heroIconUrl, heroSlugFromInternal } from "../../utils/imageUrls";
import ItemTimeline from "../timeline/ItemTimeline";
import LoadingSkeleton from "../timeline/LoadingSkeleton";
import ErrorBanner from "../timeline/ErrorBanner";

function MainPanel() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const { data, isLoading, error, selectedItemId, selectItem, clear } =
    useRecommendation();

  return (
    <main className="flex-1 bg-bg-primary overflow-y-auto p-6">
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
              <span className="text-gray-200 font-semibold text-sm">
                {selectedHero.localized_name}
              </span>
              <span className="text-gray-500 text-xs">Item Build</span>
            </div>
          )}

          <ItemTimeline
            data={data}
            selectedItemId={selectedItemId}
            onSelectItem={selectItem}
          />
        </div>
      )}

      {/* Empty states */}
      {!data && !isLoading && !error && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 text-sm">
            {selectedHero
              ? "Configure your draft and click Get Item Build to see recommendations"
              : "Select a hero from the sidebar to get started"}
          </p>
        </div>
      )}
    </main>
  );
}

export default MainPanel;
