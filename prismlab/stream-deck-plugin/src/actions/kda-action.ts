import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function buildKdaSvg(state: GsiState): string {
  const kColor = state.kills >= 10 ? "#6aff97" : "#fff";
  const dColor = state.deaths >= 5 ? "#ff5555" : "#fff";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    `<text x="36" y="22" text-anchor="middle" fill="#888" font-family="Arial" font-size="10">KDA</text>` +
    `<text x="36" y="42" text-anchor="middle" fill="#fff" font-family="Arial" font-size="16" font-weight="bold">` +
    `<tspan fill="${kColor}">${state.kills}</tspan>` +
    `<tspan fill="#555">/</tspan>` +
    `<tspan fill="${dColor}">${state.deaths}</tspan>` +
    `<tspan fill="#555">/</tspan>` +
    `<tspan fill="#aaa">${state.assists}</tspan>` +
    `</text>` +
    `<text x="36" y="60" text-anchor="middle" fill="#555" font-family="Arial" font-size="10">Lv${state.hero_level}</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.kda" })
export class KdaAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildKdaSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
