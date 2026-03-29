import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function buildRoshSvg(state: GsiState): string {
  const rs = state.roshan_state;
  let label: string;
  let color: string;
  let sublabel: string;
  if (rs === "alive") {
    label = "ALIVE"; color = "#6aff97"; sublabel = "Rosh up";
  } else if (rs === "respawning") {
    label = "DEAD"; color = "#ff5555"; sublabel = "Respawning";
  } else {
    label = "?"; color = "#888"; sublabel = "Unknown";
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    `<text x="36" y="28" text-anchor="middle" fill="${color}" font-family="Arial" font-size="20" font-weight="bold">${label}</text>` +
    `<text x="36" y="46" text-anchor="middle" fill="#888" font-family="Arial" font-size="11">${sublabel}</text>` +
    `<text x="36" y="62" text-anchor="middle" fill="#333" font-family="Arial" font-size="9">ROSHAN</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.rosh" })
export class RoshAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildRoshSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
