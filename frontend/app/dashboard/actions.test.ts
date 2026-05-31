import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the Supabase server client. createClient() returns an object exposing
// auth.getUser() and from(table) → a chainable query builder. loadActivitySummary
// issues two queries against `workouts`:
//   1. latest: …order().limit().maybeSingle()  → resolves via maybeSingle()
//   2. week:   …gte()                            → the builder is awaited directly
// So the builder is both chainable AND thenable; maybeSingle() returns its own result.
const mockGetUser = vi.fn();
const fromImpl = vi.fn();

vi.mock("@/lib/supabase/server", () => ({
  createClient: async () => ({
    auth: { getUser: mockGetUser },
    from: fromImpl,
  }),
}));

import { loadActivitySummary } from "./actions";

type Row = Record<string, unknown>;

/** A chainable builder: every method returns `this`; it resolves to `weekResult`
 *  when awaited, and maybeSingle() resolves to `latestResult`. */
function makeBuilder(latestResult: { data: Row | null }, weekResult: { data: Row[] | null }) {
  const builder: Record<string, unknown> = {};
  for (const m of ["select", "eq", "order", "limit", "gte"]) {
    builder[m] = vi.fn(() => builder);
  }
  builder.maybeSingle = vi.fn(async () => latestResult);
  // Thenable so `await supabase.from(...).…gte(...)` yields weekResult.
  builder.then = (resolve: (v: { data: Row[] | null }) => unknown) => resolve(weekResult);
  return builder;
}

beforeEach(() => {
  mockGetUser.mockReset();
  fromImpl.mockReset();
});

describe("loadActivitySummary", () => {
  it("returns null when there is no authenticated user", async () => {
    mockGetUser.mockResolvedValue({ data: { user: null } });
    expect(await loadActivitySummary()).toBeNull();
  });

  it("maps the latest row and computes week totals", async () => {
    mockGetUser.mockResolvedValue({ data: { user: { id: "u1" } } });
    const latest = {
      started_at: "2026-05-30T06:00:00Z",
      sport: "run",
      distance_m: 10000,
      duration_seconds: 3000,
      avg_pace_s_per_km: 300,
    };
    const weekRows = [
      { distance_m: 10000, duration_seconds: 3000 },
      { distance_m: 5000, duration_seconds: 1800 },
      { distance_m: null, duration_seconds: null },
    ];
    fromImpl.mockReturnValue(makeBuilder({ data: latest }, { data: weekRows }));

    const result = await loadActivitySummary();
    expect(result).not.toBeNull();
    expect(result!.latest).toEqual(latest);
    expect(result!.week.activities).toBe(3);
    expect(result!.week.km).toBeCloseTo(15, 5); // (10000 + 5000) / 1000
    expect(result!.week.hours).toBeCloseTo((3000 + 1800) / 3600, 5);
  });

  it("returns latest=null and zeroed week when there are no workouts", async () => {
    mockGetUser.mockResolvedValue({ data: { user: { id: "u1" } } });
    fromImpl.mockReturnValue(makeBuilder({ data: null }, { data: [] }));

    const result = await loadActivitySummary();
    expect(result).toEqual({
      latest: null,
      week: { activities: 0, km: 0, hours: 0 },
    });
  });

  // Criterion A3: Strava not connected is the SAME code path as "no workouts"
  // — the workouts table is simply empty, the loader returns latest:null. There
  // is no connection-status branch in loadActivitySummary, so the empty-state
  // test above already covers it. Asserting it explicitly for documentation.
  it("treats a never-synced (Strava not connected) account like no workouts", async () => {
    mockGetUser.mockResolvedValue({ data: { user: { id: "u1" } } });
    fromImpl.mockReturnValue(makeBuilder({ data: null }, { data: null }));

    const result = await loadActivitySummary();
    expect(result).toEqual({
      latest: null,
      week: { activities: 0, km: 0, hours: 0 },
    });
  });

  // Criterion A5 (code half): the loader must scope every query to the
  // authenticated user via .eq("user_id", user.id). The RLS owner-read policy
  // on `workouts` lives in Postgres, not this code, so it is NOT COVERABLE in a
  // unit test — this asserts the application-level scoping only.
  it("scopes every workouts query to .eq('user_id', user.id)", async () => {
    mockGetUser.mockResolvedValue({ data: { user: { id: "tenant-A" } } });

    const eqCalls: Array<[string, unknown]> = [];
    const fromTables: string[] = [];
    function trackingBuilder() {
      const builder: Record<string, unknown> = {};
      for (const m of ["select", "order", "limit", "gte"]) {
        builder[m] = vi.fn(() => builder);
      }
      builder.eq = vi.fn((col: string, val: unknown) => {
        eqCalls.push([col, val]);
        return builder;
      });
      builder.maybeSingle = vi.fn(async () => ({ data: null }));
      builder.then = (resolve: (v: { data: Row[] | null }) => unknown) => resolve({ data: [] });
      return builder;
    }
    fromImpl.mockImplementation((table: string) => {
      fromTables.push(table);
      return trackingBuilder();
    });

    await loadActivitySummary();

    // Both the latest-query and the trailing-7-day query scope to the user.
    expect(eqCalls.length).toBe(2);
    for (const [col, val] of eqCalls) {
      expect(col).toBe("user_id");
      expect(val).toBe("tenant-A");
    }
  });

  // Criterion A6: loadActivitySummary reads Supabase directly — it must NOT
  // make a network fetch to a new backend endpoint.
  it("does not call fetch (direct-Supabase, no new backend endpoint)", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    mockGetUser.mockResolvedValue({ data: { user: { id: "u1" } } });
    fromImpl.mockReturnValue(makeBuilder({ data: null }, { data: [] }));

    await loadActivitySummary();

    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
