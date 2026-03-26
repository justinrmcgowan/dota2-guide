import { useGsiStore } from "../../stores/gsiStore";

function formatGameClock(seconds: number): string {
  const negative = seconds < 0;
  const abs = Math.abs(seconds);
  const mins = Math.floor(abs / 60);
  const secs = abs % 60;
  return `${negative ? "-" : ""}${mins}:${String(secs).padStart(2, "0")}`;
}

function GameClock() {
  const gsiStatus = useGsiStore((s) => s.gsiStatus);
  const liveState = useGsiStore((s) => s.liveState);

  if (gsiStatus !== "connected") return null;
  if (!liveState) return null;
  if (liveState.game_state !== "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS") return null;

  return (
    <span
      className="text-cyan-accent text-sm font-mono font-semibold"
      data-testid="game-clock"
    >
      {formatGameClock(liveState.game_clock)}
    </span>
  );
}

export default GameClock;
