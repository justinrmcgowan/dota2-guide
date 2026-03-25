import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

describe("GsiStatusIndicator", () => {
  beforeEach(() => {
    // Will import and reset gsiStore once it's created
  });

  it.todo("renders GSI label text");
  it.todo("shows gray dot when gsiStatus is idle");
  it.todo("shows green dot when gsiStatus is connected");
  it.todo("shows red dot when gsiStatus is lost");
  it.todo("tooltip shows GSI status and WebSocket status");
  it.todo("tooltip shows game time when connected with liveState");
});
