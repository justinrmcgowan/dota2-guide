import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function buildGoldSvg(state: GsiState): string {
  const g = state.gold;
  const goldStr = g >= 1000 ? `${(g / 1000).toFixed(1)}k` : `${g}`;
  const alive = state.is_alive ? "#FFD700" : "#888";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    `<text x="36" y="26" text-anchor="middle" fill="${alive}" font-family="Arial" font-size="22" font-weight="bold">${goldStr}</text>` +
    `<text x="36" y="44" text-anchor="middle" fill="#aaa" font-family="Arial" font-size="13">${state.gpm} GPM</text>` +
    `<text x="36" y="62" text-anchor="middle" fill="#555" font-family="Arial" font-size="10">GOLD</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.gold" })
export class GoldAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildGoldSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
