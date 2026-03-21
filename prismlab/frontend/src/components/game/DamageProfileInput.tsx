import { useGameStore } from "../../stores/gameStore";
import { DAMAGE_PRESETS } from "../../utils/constants";

const SLIDER_CONFIG = [
  { key: "physical" as const, label: "Physical", accent: "#9ca3af" },
  { key: "magical" as const, label: "Magical", accent: "#00d4ff" },
  { key: "pure" as const, label: "Pure", accent: "#a855f7" },
] as const;

function DamageProfileInput() {
  const damageProfile = useGameStore((s) => s.damageProfile);
  const setDamageProfile = useGameStore((s) => s.setDamageProfile);

  const current = damageProfile ?? { physical: 0, magical: 0, pure: 0 };

  const isPresetActive = (preset: (typeof DAMAGE_PRESETS)[number]) =>
    damageProfile !== null &&
    damageProfile.physical === preset.profile.physical &&
    damageProfile.magical === preset.profile.magical &&
    damageProfile.pure === preset.profile.pure;

  const handleSliderChange = (
    key: "physical" | "magical" | "pure",
    value: number,
  ) => {
    setDamageProfile({ ...current, [key]: value });
  };

  return (
    <div className="space-y-3">
      {/* Quick presets */}
      <div className="flex flex-wrap gap-1.5">
        {DAMAGE_PRESETS.map((preset) => {
          const active = isPresetActive(preset);
          return (
            <button
              key={preset.label}
              onClick={() =>
                setDamageProfile({
                  physical: preset.profile.physical,
                  magical: preset.profile.magical,
                  pure: preset.profile.pure,
                })
              }
              className={`px-2 py-1 text-[10px] font-medium rounded-md border transition-colors ${
                active
                  ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
                  : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
              }`}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Sliders */}
      <div className="space-y-2">
        {SLIDER_CONFIG.map(({ key, label, accent }) => (
          <div key={key} className="flex items-center gap-2">
            <label className="text-[10px] text-gray-400 w-14 shrink-0">
              {label}:
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={current[key]}
              onChange={(e) => handleSliderChange(key, Number(e.target.value))}
              className="flex-1 h-1.5 rounded-lg appearance-none bg-bg-elevated cursor-pointer"
              style={{ accentColor: accent }}
            />
            <span className="text-[10px] text-gray-300 w-8 text-right tabular-nums">
              {current[key]}%
            </span>
          </div>
        ))}
      </div>

      {/* Hint when not set */}
      {damageProfile === null && (
        <p className="text-[10px] text-gray-600 italic">
          Set damage from death screen
        </p>
      )}
    </div>
  );
}

export default DamageProfileInput;
