import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Brand } from "./brand";

// Smoke test that doubles as proof the Vitest + RTL harness works.
describe("Brand", () => {
  it("renders the wordmark linking home by default", () => {
    render(<Brand />);
    const link = screen.getByRole("link", { name: /evolverun/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/");
  });

  it("honours a custom href", () => {
    render(<Brand href="/dashboard" />);
    expect(screen.getByRole("link", { name: /evolverun/i })).toHaveAttribute(
      "href",
      "/dashboard",
    );
  });
});
