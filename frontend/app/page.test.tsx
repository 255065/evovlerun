import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "./page";

// The landing page is an async server component, so we resolve its JSX first
// (with empty searchParams) and render that.
describe("LandingPage", () => {
  it("renders the hero headline and a Get started link to /signup", async () => {
    const ui = await LandingPage({ searchParams: Promise.resolve({}) });
    render(ui);

    expect(
      screen.getByRole("heading", { level: 1 }),
    ).toHaveTextContent(/understand your training with\s*ai/i);

    const getStarted = screen
      .getAllByRole("link", { name: /get started/i })
      .find((link) => link.getAttribute("href") === "/signup");
    expect(getStarted).toBeDefined();
  });
});
