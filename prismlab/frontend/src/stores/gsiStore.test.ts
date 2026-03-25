import { describe, it, expect, beforeEach } from "vitest";

describe("gsiStore", () => {
  beforeEach(() => {
    // Will import and reset store once gsiStore.ts is created
  });

  it.todo("initializes with idle gsiStatus and disconnected wsStatus");
  it.todo("updateLiveState sets liveState and gsiStatus to connected");
  it.todo("updateLiveState sets lastUpdate to current timestamp");
  it.todo("setWsStatus updates wsStatus field");
  it.todo("gsiStatus becomes lost when WS disconnects while GSI was connected");
  it.todo("clearLiveState resets liveState and gsiStatus to idle");
});
