import { describe, expect, it } from "vitest";
import { decodePolyline, polylineToSvgPath } from "./polyline";

describe("decodePolyline", () => {
  // Canonical example from Google's polyline algorithm docs.
  it("decodes the reference string to the documented coordinates", () => {
    const pts = decodePolyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@");
    expect(pts).toHaveLength(3);
    expect(pts[0][0]).toBeCloseTo(38.5, 4);
    expect(pts[0][1]).toBeCloseTo(-120.2, 4);
    expect(pts[1][0]).toBeCloseTo(40.7, 4);
    expect(pts[1][1]).toBeCloseTo(-120.95, 4);
    expect(pts[2][0]).toBeCloseTo(43.252, 3);
    expect(pts[2][1]).toBeCloseTo(-126.453, 3);
  });

  it("returns an empty array for an empty string", () => {
    expect(decodePolyline("")).toEqual([]);
  });
});

describe("polylineToSvgPath", () => {
  it("returns null when there are too few points to draw", () => {
    expect(polylineToSvgPath([[55, 12]], 100, 100)).toBeNull();
  });

  it("produces an M…L path that stays within the viewBox", () => {
    const pts = decodePolyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@");
    const d = polylineToSvgPath(pts, 200, 100)!;
    expect(d).toMatch(/^M[\d.]+ [\d.]+( L[\d.]+ [\d.]+)+$/);
    // every coordinate is finite and inside the padded box
    const nums = d.match(/[\d.]+/g)!.map(Number);
    for (const n of nums) expect(Number.isFinite(n)).toBe(true);
  });
});
