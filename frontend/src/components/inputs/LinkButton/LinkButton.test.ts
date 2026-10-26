import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/svelte";

import LinkButton from "./LinkButton.svelte";
import { createRawSnippet } from "svelte";

const label = createRawSnippet(() => ({ render: () => "<span>Open</span>" }));

describe("LinkButton", () => {
  it("renders a real link when given a destination", () => {
    render(LinkButton, { href: "/consultations", children: label });

    const link = screen.getByRole("link", { name: "Open" });
    expect(link).toHaveAttribute("href", "/consultations");
    expect(link).not.toHaveAttribute("type");
  });

  it("renders a button for an in-page action", async () => {
    const handleClick = vi.fn();
    render(LinkButton, { handleClick, ariaExpanded: false, children: label });

    const button = screen.getByRole("button", { name: "Open" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveAttribute("aria-expanded", "false");
    await fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it("disables the button and ignores clicks while disabled", async () => {
    const handleClick = vi.fn();
    render(LinkButton, { handleClick, disabled: true, children: label });

    const button = screen.getByRole("button", { name: "Open" });
    expect(button).toBeDisabled();
    await fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("uses the accessible name over the visible text when given", () => {
    render(LinkButton, {
      handleClick: vi.fn(),
      ariaLabel: "Remove link to Q2",
      children: label,
    });

    expect(
      screen.getByRole("button", { name: "Remove link to Q2" }),
    ).toBeInTheDocument();
  });
});
