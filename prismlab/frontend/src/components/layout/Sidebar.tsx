import HeroPicker from "../draft/HeroPicker";

function Sidebar() {
  return (
    <aside className="w-80 bg-bg-secondary border-r border-bg-elevated flex flex-col overflow-hidden shrink-0">
      <div className="p-4 flex-1 overflow-y-auto">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Your Hero
        </h2>
        <HeroPicker excludedHeroIds={new Set()} />
        {/* Future Phase 2 components: RoleSelector, PlaystyleSelector, etc. */}
      </div>
    </aside>
  );
}

export default Sidebar;
