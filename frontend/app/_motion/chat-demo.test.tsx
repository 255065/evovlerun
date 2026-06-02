import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatDemo } from "./chat-demo";

// Content is always rendered in the DOM (the animation only drives the
// entrance), so the demo's prompt, tools, chart labels, and summary are all
// queryable regardless of the reveal step.
describe("ChatDemo", () => {
  it("renders the prompt, EvolveRun tool chips, the JAN–MAR chart, and the summary", () => {
    render(<ChatDemo />);

    expect(
      screen.getByText(/compare my easy running pace trend this year/i),
    ).toBeInTheDocument();

    expect(screen.getByText("USING EVOLVERUN TOOLS")).toBeInTheDocument();
    expect(screen.getByText("compare-strava-periods")).toBeInTheDocument();
    expect(screen.getByText("chart-easy-pace-trend")).toBeInTheDocument();
    expect(screen.getByText("get-coros-training-zones")).toBeInTheDocument();

    expect(screen.getByText("JAN — MAR · PACE VS HR")).toBeInTheDocument();
    expect(screen.getByText("Jan")).toBeInTheDocument();
    expect(screen.getByText("Mar")).toBeInTheDocument();
    expect(screen.getByText("149 bpm")).toBeInTheDocument();
    expect(screen.getByText("145 bpm")).toBeInTheDocument();

    expect(
      screen.getByText(/your easy-run pace improved each month/i),
    ).toBeInTheDocument();
  });
});
