import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "./page";

describe("Training EmptyState", () => {
  it("links 'Open Claude' to claude.ai in a new tab", () => {
    render(<EmptyState />);
    const claude = screen.getByRole("link", { name: /open claude/i });
    expect(claude).toHaveAttribute("href", "https://claude.ai");
    expect(claude).toHaveAttribute("target", "_blank");
    expect(claude).toHaveAttribute("rel", "noreferrer");
  });

  it("links 'Set up the connector' to /dashboard/mcp", () => {
    render(<EmptyState />);
    expect(screen.getByRole("link", { name: /set up the connector/i })).toHaveAttribute(
      "href",
      "/dashboard/mcp",
    );
  });
});
