import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection, GsiState } from "../connection";

function shortItem(name: string): string {
  if (!name) return "---";
  // Strip common Dota prefixes for brevity
  const n = name.replace(/^item_/, "").replace(/_/g, " ");
  return n.length > 8 ? n.slice(0, 8) : n;
}

function buildItemsSvg(state: GsiState): string {
  const inv = state.items_inventory;
  // 3 columns, 2 rows
  const slots = [0, 1, 2, 3, 4, 5].map((i) => shortItem(inv[i] ?? ""));
  const col = [12, 36, 60];
  const row = [20, 44];
  let texts = "";
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 3; c++) {
      const label = slots[r * 3 + c];
      const fill = label === "---" ? "#333" : "#00d4ff";
      texts += `<text x="${col[c]}" y="${row[r]}" text-anchor="middle" fill="${fill}" font-family="Arial" font-size="8">${label}</text>`;
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">` +
    `<rect width="72" height="72" fill="#1a1a2e"/>` +
    texts +
    `<text x="36" y="64" text-anchor="middle" fill="#333" font-family="Arial" font-size="9">ITEMS</text>` +
    `</svg>`;
}

@action({ UUID: "com.prismlab.dota2.items" })
export class ItemsAction extends SingletonAction {
  override onWillAppear(_ev: WillAppearEvent): void {
    if (backendConnection.state) this._render(backendConnection.state);
  }

  public handleState(state: GsiState): void {
    this._render(state);
  }

  private _render(state: GsiState): void {
    const svg = buildItemsSvg(state);
    this.actions.forEach((a) => {
      a.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      a.setTitle("");
    });
  }
}
