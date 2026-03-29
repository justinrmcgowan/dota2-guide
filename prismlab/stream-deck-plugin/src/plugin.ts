/**
 * Prismlab Dota 2 Stream Deck Plugin — Entry Point
 *
 * Order requirements (from SDK docs):
 *   1. Import / instantiate actions
 *   2. Register actions with streamDeck.actions.registerAction()
 *   3. Wire backendConnection.onState() listeners
 *   4. Call streamDeck.connect() LAST
 */
import streamDeck from "@elgato/streamdeck";
import { backendConnection } from "./connection";
import { GoldAction } from "./actions/gold-action";
import { KdaAction } from "./actions/kda-action";
import { ClockAction } from "./actions/clock-action";
import { ItemsAction } from "./actions/items-action";
import { RoshAction } from "./actions/rosh-action";
import { TowersAction } from "./actions/towers-action";

// Instantiate actions
const goldAction = new GoldAction();
const kdaAction = new KdaAction();
const clockAction = new ClockAction();
const itemsAction = new ItemsAction();
const roshAction = new RoshAction();
const towersAction = new TowersAction();

// Register all actions BEFORE connect()
streamDeck.actions.registerAction(goldAction);
streamDeck.actions.registerAction(kdaAction);
streamDeck.actions.registerAction(clockAction);
streamDeck.actions.registerAction(itemsAction);
streamDeck.actions.registerAction(roshAction);
streamDeck.actions.registerAction(towersAction);

// Wire state updates to all actions
backendConnection.onState((state) => {
  goldAction.handleState(state);
  kdaAction.handleState(state);
  clockAction.handleState(state);
  itemsAction.handleState(state);
  roshAction.handleState(state);
  towersAction.handleState(state);
});

// Read user-configured backend URL from global settings, then connect
streamDeck.settings
  .getGlobalSettings<{ backendUrl?: string }>()
  .then(({ backendUrl }) => {
    backendConnection.connect(backendUrl ?? "ws://localhost:8420/ws");
  })
  .catch(() => {
    backendConnection.connect("ws://localhost:8420/ws");
  });

// Re-connect when user changes URL in property inspector
streamDeck.settings.onDidReceiveGlobalSettings(({ settings }) => {
  const url = (settings as { backendUrl?: string }).backendUrl;
  if (url) {
    backendConnection.reconnect(url);
  }
});

// MUST be called last
streamDeck.connect();
