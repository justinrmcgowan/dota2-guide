import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function formatClock(seconds: number): string {
  if (seconds < 0) return "PRE";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function buildClockSvg(state: GsiState): string {
  const timeStr = formatClock(state.game_clock);
  const isDay = state.game_clock >= 0 && state.game_clock % 300 < 150;
  const timeColor = state.game_clock < 0 ? "#888" : "#00d4ff";
  const phaseLabel = state.game_clock < 0 ? "DRAFT" : isDay ? "DAY" : "NIGHT";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    `<text x="36" y="30" text-anchor="middle" fill="${timeColor}" font-family="Arial" font-size="22" font-weight="bold">${timeStr}</text>` +
    `<text x="36" y="50" text-anchor="middle" fill="#555" font-family="Arial" font-size="11">${phaseLabel}</text>` +
    `<text x="36" y="64" text-anchor="middle" fill="#333" font-family="Arial" font-size="9">CLOCK</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.clock" })
export class ClockAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildClockSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
