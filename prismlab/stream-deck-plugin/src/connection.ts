/**
 * Module-level singleton WebSocket connection to the Prismlab backend.
 *
 * Connects to ws://<host>:8420/ws, applies exponential-backoff reconnect on
 * close, stores the latest GsiState in memory, and notifies registered listeners.
 * All 6 action types share this single connection.
 */
import WebSocket from "ws";

export interface GsiState {
  hero_name: string;
  hero_id: number;
  hero_level: number;
  has_aghanims_shard: boolean;
  has_aghanims_scepter: boolean;
  gold: number;
  gpm: number;
  net_worth: number;
  kills: number;
  deaths: number;
  assists: number;
  items_inventory: string[];
  items_backpack: string[];
  items_neutral: string;
  game_clock: number;
  game_state: string;
  match_id: string;
  team_side: string;
  is_alive: boolean;
  roshan_state: string;
  radiant_tower_count: number;
  dire_tower_count: number;
  timestamp: number;
}

class BackendConnection {
  private ws: WebSocket | null = null;
  private retryDelay = 1000;
  private currentUrl = "ws://localhost:8420/ws";
  public state: GsiState | null = null;
  private listeners: Array<(state: GsiState) => void> = [];

  connect(url: string): void {
    this.currentUrl = url;
    this._open(url);
  }

  reconnect(url: string): void {
    if (this.ws) {
      this.ws.removeAllListeners();
      this.ws.terminate();
      this.ws = null;
    }
    this.retryDelay = 1000;
    this.connect(url);
  }

  onState(fn: (state: GsiState) => void): void {
    this.listeners.push(fn);
  }

  private _open(url: string): void {
    try {
      this.ws = new WebSocket(url);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.ws.on("message", (raw) => {
      try {
        const msg = JSON.parse(raw.toString()) as { type: string; data: GsiState };
        if (msg.type === "game_state") {
          this.state = msg.data;
          this.listeners.forEach((fn) => fn(this.state!));
        }
      } catch {
        // Ignore malformed messages
      }
    });

    this.ws.on("open", () => {
      this.retryDelay = 1000;
    });

    this.ws.on("close", () => {
      this._scheduleReconnect();
    });

    this.ws.on("error", () => {
      // Error event always followed by close; handled there
    });
  }

  private _scheduleReconnect(): void {
    setTimeout(() => {
      this.retryDelay = Math.min(this.retryDelay * 2, 30000);
      this._open(this.currentUrl);
    }, this.retryDelay);
  }
}

export const backendConnection = new BackendConnection();
