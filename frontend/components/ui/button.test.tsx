import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "./button";

// Proves the new `asChild` Slot path: instead of rendering its own <button>,
// Button merges its props/classes onto the single child element. This is the
// only genuinely new capability of the Foundation slice worth asserting on.
describe("Button asChild", () => {
  it("renders its child as the element (anchor, not a button)", () => {
    render(
      <Button asChild>
        <a href="/x">x</a>
      </Button>,
    );

    const link = screen.getByRole("link", { name: "x" });
    expect(link).toBeInTheDocument();
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("href", "/x");
    // No <button> should be rendered when asChild is set.
    expect(screen.queryByRole("button")).toBeNull();
  });
});
