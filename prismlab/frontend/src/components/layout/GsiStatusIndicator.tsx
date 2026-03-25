import { useGsiStore } from "../../stores/gsiStore";

function GsiStatusIndicator() {
  const { gsiStatus, wsStatus, lastUpdate, liveState } = useGsiStore();

  const dotColor = {
    connected: "bg-radiant",
    idle: "bg-gray-500",
    lost: "bg-dire",
  }[gsiStatus];

  const statusLabel = {
    connected: "Connected",
    idle: "Idle",
    lost: "Lost",
  }[gsiStatus];

  // Build tooltip text per D-08
  const tooltipLines: string[] = [
    `GSI: ${statusLabel}`,
    `WebSocket: ${wsStatus}`,
  ];
  if (lastUpdate) {
    tooltipLines.push(
      `Last update: ${new Date(lastUpdate).toLocaleTimeString()}`,
    );
  }
  if (liveState?.game_clock != null && gsiStatus === "connected") {
    const mins = Math.floor(liveState.game_clock / 60);
    const secs = liveState.game_clock % 60;
    tooltipLines.push(
      `Game time: ${mins}:${String(secs).padStart(2, "0")}`,
    );
  }

  return (
    <div
      className="flex items-center gap-1.5 cursor-default"
      title={tooltipLines.join("\n")}
      data-testid="gsi-status"
    >
      <span
        className={`w-2 h-2 rounded-full ${dotColor}`}
        data-testid="gsi-dot"
      />
      <span className="text-xs text-text-muted">GSI</span>
    </div>
  );
}

export default GsiStatusIndicator;
