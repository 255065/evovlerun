import { describe, expect, it } from "vitest";
import { fmtDate, fmtSessionType } from "./format";

/**
 * Acceptance criterion D: format.ts is fully English — no Danish strings
 * remain. We can't enumerate the module's private label maps directly, so we
 * exercise the two public surfaces that carry user-facing copy:
 *   - fmtSessionType() over every known session slug (the label table)
 *   - fmtDate() (must be en-GB output, not da-DK)
 * and assert none of the output contains Danish month abbreviations or known
 * Danish session words.
 */

const SESSION_SLUGS = [
  "easy",
  "long",
  "tempo",
  "threshold",
  "intervals",
  "vo2max",
  "fartlek",
  "hills",
  "recovery",
  "race",
  "strength",
  "cross_training",
  "rest",
];

// Danish words/abbreviations that would betray a missed translation.
const DANISH_TOKENS = [
  // Danish weekday/month abbreviations and common training words.
  "rolig",
  "hvile",
  "langtur",
  "løb",
  "uge",
  "styrke",
  "tærskel",
  "maj",
  "okt",
  "søn",
  "lør",
  "tir",
  "ons",
  "tor",
  "fre",
  "man",
];

describe("format.ts is English (criterion D)", () => {
  it("every session-type label is non-empty and free of Danish tokens", () => {
    for (const slug of SESSION_SLUGS) {
      const label = fmtSessionType(slug);
      expect(label).toBeTruthy();
      // Every known slug must be mapped to a human label, not echoed raw.
      expect(label).not.toBe(slug);
      const lower = label.toLowerCase();
      for (const token of DANISH_TOKENS) {
        expect(lower).not.toContain(token);
      }
    }
  });

  it("known session slugs map to the expected English labels", () => {
    expect(fmtSessionType("easy")).toBe("Easy");
    expect(fmtSessionType("long")).toBe("Long run");
    expect(fmtSessionType("recovery")).toBe("Recovery");
    expect(fmtSessionType("rest")).toBe("Rest");
    expect(fmtSessionType("cross_training")).toBe("Cross-training");
  });

  it("fmtDate emits en-GB output (English month abbreviations)", () => {
    // 2026-05-15 → "15 May" in en-GB; "15. maj" in da-DK.
    const out = fmtDate("2026-05-15T00:00:00Z");
    expect(out).toMatch(/May/);
    expect(out.toLowerCase()).not.toContain("maj");
  });

  it("fmtDate matches the en-GB format reference exactly", () => {
    const iso = "2026-10-03T00:00:00Z";
    const expected = new Date(iso).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
    });
    expect(fmtDate(iso)).toBe(expected);
    expect(expected.toLowerCase()).not.toContain("okt");
  });
});
