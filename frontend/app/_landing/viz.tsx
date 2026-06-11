// Live visualization inside the demo chat. Receives `e` (ms within the
// current segment); all motion is derived from `e` and applied inline so it
// animates from the single rAF clock in chat-demo.tsx.

const VZ_CHART = 3700;
const clampv = (x: number) => Math.max(0, Math.min(1, x));
const easeOut = (p: number) => 1 - Math.pow(1 - clampv(p), 3);

const PACE_COLS = [
  { m: "Jan", pace: "5:23/km", bpm: "149 bpm", h: 64 },
  { m: "Feb", pace: "5:17/km", bpm: "147 bpm", h: 80 },
  { m: "Mar", pace: "5:08/km", bpm: "145 bpm", h: 98 },
];

export function VizPace({ e }: { e: number }) {
  return (
    <div className="bubble viz">
      <div className="viz-h">
        <span>Easy runs</span>
        <span className="mid">Jan — March</span>
        <span>Pace vs HR</span>
      </div>
      <div className="bars">
        {PACE_COLS.map((c, i) => {
          const f = easeOut((e - (VZ_CHART + i * 170)) / 620);
          return (
            <div key={c.m} className="bar-col">
              <div className="bar-pace" style={{ opacity: f }}>
                {c.pace}
              </div>
              <div className="bar" style={{ height: f * c.h + "%" }} />
            </div>
          );
        })}
      </div>
      <div className="bar-foot">
        {PACE_COLS.map((c) => (
          <div key={c.m}>
            <div className="m">{c.m}</div>
            <div className="b">{c.bpm}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
