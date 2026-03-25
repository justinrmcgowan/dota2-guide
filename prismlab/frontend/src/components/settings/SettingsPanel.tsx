import { useState } from "react";

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const [host, setHost] = useState("");
  const [downloading, setDownloading] = useState(false);

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

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        data-testid="settings-backdrop"
      />
      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-96 bg-bg-secondary border-l border-bg-elevated z-50 overflow-y-auto shadow-2xl">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-cyan-accent">Settings</h2>
            <button
              onClick={onClose}
              className="text-text-muted hover:text-gray-100 transition-colors"
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
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Game State Integration
            </h3>

            {/* IP Input */}
            <div>
              <label
                htmlFor="gsi-host-input"
                className="block text-sm text-text-muted mb-1"
              >
                Your PC's IP address
              </label>
              <input
                id="gsi-host-input"
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="e.g. 192.168.1.100"
                className="w-full px-3 py-2 bg-bg-primary border border-bg-elevated rounded text-gray-100 placeholder-gray-600 focus:border-cyan-accent focus:outline-none text-sm"
              />
            </div>

            {/* Port Display */}
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Port
              </label>
              <div className="px-3 py-2 bg-bg-primary border border-bg-elevated rounded text-gray-400 text-sm">
                8421
              </div>
            </div>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              disabled={!host.trim() || downloading}
              className="w-full py-2 px-4 bg-cyan-accent/20 text-cyan-accent border border-cyan-accent/30 rounded font-medium text-sm hover:bg-cyan-accent/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {downloading ? "Generating..." : "Download .cfg file"}
            </button>

            {/* Step-by-step Instructions (D-04) */}
            <div className="mt-6 space-y-3">
              <h4 className="text-sm font-semibold text-gray-300">
                Setup Instructions
              </h4>
              <ol className="list-decimal list-inside space-y-2 text-sm text-text-muted">
                <li>
                  Enter your PC's local IP address above (find it with{" "}
                  <code className="text-cyan-accent bg-bg-primary px-1 rounded">
                    ipconfig
                  </code>{" "}
                  on Windows or{" "}
                  <code className="text-cyan-accent bg-bg-primary px-1 rounded">
                    ifconfig
                  </code>{" "}
                  on Mac/Linux)
                </li>
                <li>
                  Click{" "}
                  <strong className="text-gray-300">
                    Download .cfg file
                  </strong>
                </li>
                <li>
                  Place the downloaded file in:
                  <code className="block mt-1 text-cyan-accent bg-bg-primary px-2 py-1 rounded text-xs break-all">
                    Steam/steamapps/common/dota 2
                    beta/game/dota/cfg/gamestate_integration/
                  </code>
                </li>
                <li>
                  Create the{" "}
                  <code className="text-cyan-accent bg-bg-primary px-1 rounded">
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
        </div>
      </div>
    </>
  );
}

export default SettingsPanel;
