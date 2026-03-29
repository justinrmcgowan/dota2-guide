import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function buildTowersSvg(state: GsiState): string {
  const rad = state.radiant_tower_count;
  const dire = state.dire_tower_count;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    `<text x="36" y="18" text-anchor="middle" fill="#888" font-family="Arial" font-size="10">TOWERS</text>` +
    `<text x="20" y="42" text-anchor="middle" fill="#6aff97" font-family="Arial" font-size="26" font-weight="bold">${rad}</text>` +
    `<text x="36" y="42" text-anchor="middle" fill="#555" font-family="Arial" font-size="18">-</text>` +
    `<text x="52" y="42" text-anchor="middle" fill="#ff5555" font-family="Arial" font-size="26" font-weight="bold">${dire}</text>` +
    `<text x="20" y="58" text-anchor="middle" fill="#6aff97" font-family="Arial" font-size="9">RAD</text>` +
    `<text x="52" y="58" text-anchor="middle" fill="#ff5555" font-family="Arial" font-size="9">DIRE</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.towers" })
export class TowersAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildTowersSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
