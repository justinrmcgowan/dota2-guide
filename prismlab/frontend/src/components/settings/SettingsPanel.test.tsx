import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SettingsPanel from "./SettingsPanel";

describe("SettingsPanel", () => {
  it("renders nothing when open is false", () => {
    const { container } = render(
      <SettingsPanel open={false} onClose={vi.fn()} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders panel with Settings heading when open is true", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("renders IP input field", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    const input = screen.getByPlaceholderText("e.g. 192.168.1.100");
    expect(input).toBeTruthy();
  });

  it("renders port display showing 8421", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    expect(screen.getByText("8421")).toBeTruthy();
  });

  it("renders Download .cfg file button", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    const button = screen.getByRole("button", { name: /download \.cfg file/i });
    expect(button).toBeTruthy();
  });

  it("disables download button when IP is empty", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    const button = screen.getByRole("button", { name: /download \.cfg file/i });
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("renders setup instructions with Steam path", () => {
    render(<SettingsPanel open={true} onClose={vi.fn()} />);
    expect(
      screen.getByText(/steamapps\/common\/dota 2 beta/),
    ).toBeTruthy();
  });

  it("calls onClose when backdrop is clicked", () => {
    const onClose = vi.fn();
    render(<SettingsPanel open={true} onClose={onClose} />);
    const backdrop = screen.getByTestId("settings-backdrop");
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
