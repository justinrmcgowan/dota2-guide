import { useState, useEffect } from "react";
import { isValidSteamId } from "../../utils/steamId";
import { api } from "../../api/client";
import type { EngineBudget } from "../../types/recommendation";
import { useAudioStore } from "../../stores/audioStore";

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

type EngineMode = "fast" | "auto" | "deep";

const ENGINE_MODES: { value: EngineMode; label: string; badge?: string; description: string }[] = [
  { value: "fast", label: "Fast", description: "Rules only. Instant. No AI reasoning." },
  { value: "auto", label: "Auto", badge: "default", description: "Local AI + Claude fallback. Best balance." },
  { value: "deep", label: "Deep", description: "Always Claude API. Full reasoning. Highest cost." },
];

function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const [host, setHost] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [steamId, setSteamId] = useState(
    () => localStorage.getItem("prismlab_steam_id") ?? "",
  );
  const [steamIdValid, setSteamIdValid] = useState(true);
  const [mode, setMode] = useState<EngineMode>(
    () => (localStorage.getItem("prismlab_engine_mode") as EngineMode) ?? "auto",
  );
  const [budget, setBudget] = useState<EngineBudget | null>(null);

  const { enabled: audioEnabled, volume: audioVolume, setEnabled: setAudioEnabled, setVolume: setAudioVolume } = useAudioStore();

  // Pre-fill Steam ID from backend .env if localStorage is empty (D-10)
  useEffect(() => {
    if (!localStorage.getItem("prismlab_steam_id")) {
      api
        .getSettingsDefaults()
        .then((defaults) => {
          if (defaults.steam_id) {
            setSteamId(defaults.steam_id);
            localStorage.setItem("prismlab_steam_id", defaults.steam_id);
          }
        })
        .catch(() => {}); // Silent fail -- not critical
    }
  }, []);

  // Fetch budget status when panel opens
  useEffect(() => {
    if (open) {
      api.getEngineBudget().then(setBudget).catch(() => {}); // Silent fail -- not critical
    }
  }, [open]);

  const handleModeChange = (value: EngineMode) => {
    setMode(value);
    localStorage.setItem("prismlab_engine_mode", value);
  };

  if (!open) return null;

  const handleDownload = async () => {
    if (!host.trim()) return;
    setDownloading(true);
    try {
      const res = await fetch(
        `/api/gsi-config?host=${encodeURIComponent(host.trim())}&port=8421`,
      );
      if (!res.ok) throw new Error("Failed to generate config");
      const text = await res.text();
      const blob = new Blob([text], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "gamestate_integration_prismlab.cfg";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Config download failed:", err);
    } finally {
      setDownloading(false);
    }
  };

  const handleSteamIdChange = (value: string) => {
    setSteamId(value);
    if (value === "") {
      setSteamIdValid(true);
      localStorage.removeItem("prismlab_steam_id");
    } else if (isValidSteamId(value)) {
      setSteamIdValid(true);
      localStorage.setItem("prismlab_steam_id", value);
    } else {
      setSteamIdValid(false);
    }
  };

  return (
    <>
      {/* Backdrop — blood-glass (D-17) */}
      <div
        className="fixed inset-0 bg-primary-container/25 backdrop-blur-md z-40"
        onClick={onClose}
        data-testid="settings-backdrop"
      />
      {/* Panel — surface-container-highest with ambient crimson glow (D-09, D-15) */}
      <div className="fixed right-0 top-0 h-full w-96 bg-surface-container-highest z-50 overflow-y-auto shadow-glow">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-secondary font-display">Settings</h2>
            <button
              onClick={onClose}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label="Close settings"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-5 h-5"
              >
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </div>

          {/* GSI Configuration Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-on-surface uppercase tracking-wider">
              Game State Integration
            </h3>

            {/* IP Input — Sacrificial Table pattern (D-05) */}
            <div>
              <label
                htmlFor="gsi-host-input"
                className="block text-sm text-on-surface-variant mb-1"
              >
                Your PC's IP address
              </label>
              <input
                id="gsi-host-input"
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="e.g. 192.168.1.100"
                className="w-full px-3 py-2 bg-surface-container-lowest border-b border-outline-variant/15 text-on-surface placeholder-on-surface-variant/40 focus:border-primary focus:outline-none text-sm"
              />
            </div>

            {/* Port Display — Sacrificial Table pattern */}
            <div>
              <label className="block text-sm text-on-surface-variant mb-1">
                Port
              </label>
              <div className="px-3 py-2 bg-surface-container-lowest border-b border-outline-variant/15 text-on-surface-variant text-sm">
                8421
              </div>
            </div>

            {/* Download Button — Blade pattern (D-05) */}
            <button
              onClick={handleDownload}
              disabled={!host.trim() || downloading}
              className="w-full py-2 px-4 bg-primary-container text-on-surface border border-outline-variant/15 font-medium text-sm hover:outline hover:outline-1 hover:outline-[#AA8986] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {downloading ? "Generating..." : "Download .cfg file"}
            </button>

            {/* Step-by-step Instructions */}
            <div className="mt-6 space-y-3">
              <h4 className="text-sm font-semibold text-on-surface">
                Setup Instructions
              </h4>
              <ol className="list-decimal list-inside space-y-2 text-sm text-on-surface-variant">
                <li>
                  Enter your PC's local IP address above (find it with{" "}
                  <code className="text-primary bg-surface-container-lowest px-1">
                    ipconfig
                  </code>{" "}
                  on Windows or{" "}
                  <code className="text-primary bg-surface-container-lowest px-1">
                    ifconfig
                  </code>{" "}
                  on Mac/Linux)
                </li>
                <li>
                  Click{" "}
                  <strong className="text-on-surface">
                    Download .cfg file
                  </strong>
                </li>
                <li>
                  Place the downloaded file in:
                  <code className="block mt-1 text-primary bg-surface-container-lowest px-2 py-1 text-xs break-all">
                    Steam/steamapps/common/dota 2
                    beta/game/dota/cfg/gamestate_integration/
                  </code>
                </li>
                <li>
                  Create the{" "}
                  <code className="text-primary bg-surface-container-lowest px-1">
                    gamestate_integration
                  </code>{" "}
                  folder if it doesn't exist
                </li>
                <li>Restart Dota 2</li>
                <li>
                  Start a game -- the GSI indicator should turn{" "}
                  <span className="text-radiant">green</span>
                </li>
              </ol>
            </div>
          </div>

          {/* Steam ID Section */}
          <div className="space-y-4 mt-8">
            <h3 className="text-sm font-semibold text-on-surface uppercase tracking-wider">
              Steam ID
            </h3>

            <div>
              <label
                htmlFor="steam-id-input"
                className="block text-sm text-on-surface-variant mb-1"
              >
                Your Steam ID (64-bit)
              </label>
              <input
                id="steam-id-input"
                type="text"
                value={steamId}
                onChange={(e) => handleSteamIdChange(e.target.value)}
                placeholder="e.g. 76561198353796011"
                className={`w-full px-3 py-2 bg-surface-container-lowest border-b text-on-surface placeholder-on-surface-variant/40 focus:border-primary focus:outline-none text-sm ${
                  steamIdValid
                    ? "border-outline-variant/15"
                    : "border-dire"
                }`}
              />
              {!steamIdValid && (
                <p className="text-dire text-xs mt-1">
                  Enter a valid 17-digit Steam ID
                </p>
              )}
              <p className="text-xs text-on-surface-variant/60 mt-1">
                Find your Steam ID at steamid.io — use the 17-digit ID
                from your profile URL
              </p>
            </div>
          </div>

          {/* Recommendation Engine Section */}
          <div className="space-y-4 mt-8">
            <h3 className="text-sm font-semibold text-on-surface uppercase tracking-wider">
              Recommendation Engine
            </h3>

            {/* Mode Selector -- 3 radio-style buttons (D-01, D-02) */}
            <div className="space-y-0">
              {ENGINE_MODES.map((opt) => {
                const selected = mode === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleModeChange(opt.value)}
                    className={`w-full flex items-start gap-3 px-3 py-3 bg-surface-container-lowest border-b border-outline-variant/15 text-left transition-colors hover:bg-surface-container-low ${
                      selected ? "border-l-2 border-l-primary" : "border-l-2 border-l-transparent"
                    }`}
                  >
                    {/* Radio indicator */}
                    <span className="mt-0.5 flex-shrink-0">
                      <span
                        className={`inline-block w-3.5 h-3.5 rounded-full border-2 ${
                          selected
                            ? "border-primary bg-primary"
                            : "border-on-surface-variant/40 bg-transparent"
                        }`}
                      >
                        {selected && (
                          <span className="block w-1.5 h-1.5 rounded-full bg-surface mx-auto mt-[3px]" />
                        )}
                      </span>
                    </span>
                    <span className="flex-1 min-w-0">
                      <span className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${selected ? "text-on-surface" : "text-on-surface-variant"}`}>
                          {opt.label}
                        </span>
                        {opt.badge && (
                          <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 bg-primary/15 text-primary rounded">
                            {opt.badge}
                          </span>
                        )}
                      </span>
                      <span className="block text-xs text-on-surface-variant/70 mt-0.5">
                        {opt.description}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>

            {/* API Budget Display (D-10, D-11) */}
            {budget && (
              <div className="space-y-2 mt-4">
                <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  API Budget (Monthly)
                </h4>

                {/* Progress bar */}
                <div className="w-full h-2 bg-surface-container-lowest rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      budget.exceeded
                        ? "bg-dire"
                        : budget.warning
                          ? "bg-amber-500"
                          : "bg-primary"
                    }`}
                    style={{
                      width: `${Math.min((budget.cost / budget.budget) * 100, 100)}%`,
                    }}
                  />
                </div>

                {/* Usage text */}
                <p className="text-xs text-on-surface-variant">
                  ${budget.cost.toFixed(2)} / ${budget.budget.toFixed(2)} used ({budget.requests} requests)
                </p>

                {/* Warning / exceeded messages */}
                {budget.exceeded && (
                  <p className="text-xs text-dire font-medium">
                    Budget exceeded -- Auto mode uses local AI only
                  </p>
                )}
                {budget.warning && !budget.exceeded && (
                  <p className="text-xs text-amber-500 font-medium">
                    Approaching budget limit
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Audio Coaching Section */}
          <div className="space-y-4 mt-8">
            <h3 className="text-sm font-semibold text-on-surface uppercase tracking-wider">
              Audio Coaching
            </h3>

            {/* Enable toggle — matches Engine Mode row pattern */}
            <button
              type="button"
              onClick={() => setAudioEnabled(!audioEnabled)}
              className={`w-full flex items-center justify-between px-3 py-3 bg-surface-container-lowest border-b border-outline-variant/15 text-left transition-colors hover:bg-surface-container-low ${
                audioEnabled ? "border-l-2 border-l-primary" : "border-l-2 border-l-transparent"
              }`}
              data-testid="audio-toggle"
            >
              <span className="text-sm text-on-surface">Speak item alerts</span>
              {/* Toggle pill — square corners per --radius-*: 0px design token */}
              <span
                className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center transition-colors ${
                  audioEnabled ? "bg-primary" : "bg-on-surface-variant/30"
                }`}
                aria-hidden="true"
              >
                <span
                  className={`inline-block h-3.5 w-3.5 bg-surface transform transition-transform ${
                    audioEnabled ? "translate-x-5" : "translate-x-1"
                  }`}
                />
              </span>
            </button>

            {/* Volume slider — only shown when audio is enabled */}
            {audioEnabled && (
              <div className="px-3 py-3 bg-surface-container-lowest border-b border-outline-variant/15">
                <label
                  htmlFor="audio-volume-slider"
                  className="block text-sm text-on-surface-variant mb-2"
                >
                  Volume — {Math.round(audioVolume * 100)}%
                </label>
                <input
                  id="audio-volume-slider"
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={audioVolume}
                  onChange={(e) => setAudioVolume(parseFloat(e.target.value))}
                  className="w-full accent-secondary"
                  data-testid="audio-volume-slider"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default SettingsPanel;
