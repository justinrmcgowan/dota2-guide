const SKELETON_PHASES = ["Starting", "Laning", "Core", "Late Game"] as const;

function SkeletonItemBlock() {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="w-12 h-12 bg-surface-container-high animate-pulse" />
      <div className="h-3 w-10 bg-surface-container-high animate-pulse" />
    </div>
  );
}

function SkeletonPhaseCard({ label }: { label: string }) {
  return (
    <div className="bg-surface-container-low p-[1.75rem]">
      {/* Phase header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-6 w-24 bg-surface-container-high animate-pulse" />
        <span className="text-xs text-on-surface-variant/30 animate-pulse">{label}</span>
      </div>

      {/* Item placeholders row */}
      <div className="flex flex-wrap gap-3">
        <SkeletonItemBlock />
        <SkeletonItemBlock />
        <SkeletonItemBlock />
        {label === "Core" || label === "Late Game" ? (
          <SkeletonItemBlock />
        ) : null}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      {SKELETON_PHASES.map((phase) => (
        <SkeletonPhaseCard key={phase} label={phase} />
      ))}
    </div>
  );
}

export default LoadingSkeleton;
