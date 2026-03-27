import type { BuildPathResponse, ComponentStep } from "../../types/recommendation";
import { itemImageUrl } from "../../utils/imageUrls";

interface BuildPathStepsProps {
  buildPath: BuildPathResponse;
  currentGold?: number | null;
}

function formatComponentName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function BuildPathSteps({ buildPath, currentGold = null }: BuildPathStepsProps) {
  if (!buildPath.steps || buildPath.steps.length === 0) return null;

  return (
    <div className="mt-[1rem]">
      {/* Claude's ordering justification */}
      {buildPath.build_path_notes && (
        <p className="text-on-surface-variant text-xs leading-relaxed mb-[0.75rem] italic">
          {buildPath.build_path_notes}
        </p>
      )}

      {/* Component strip: horizontal row, compact */}
      <div className="flex items-center gap-2 flex-wrap">
        {buildPath.steps.map((step: ComponentStep) => {
          const isAffordable =
            currentGold !== null &&
            step.cost !== null &&
            currentGold >= step.cost;
          const imgSrc = itemImageUrl(step.item_name);

          return (
            <div
              key={`${step.item_name}-${step.position}`}
              className="flex flex-col items-center gap-[0.25rem]"
              title={formatComponentName(step.item_name)}
            >
              {/* Step number badge */}
              <span className="text-on-surface-variant text-[10px] font-bold leading-none">
                {step.position}
              </span>
              {/* Component icon */}
              <img
                src={imgSrc}
                alt={formatComponentName(step.item_name)}
                className="w-8 h-8 object-contain rounded"
                loading="lazy"
              />
              {/* Cost with affordability highlight */}
              {step.cost !== null && (
                <span
                  className={`text-[10px] font-medium leading-none ${
                    isAffordable ? "text-radiant" : "text-on-surface-variant"
                  }`}
                >
                  {step.cost}g
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default BuildPathSteps;
