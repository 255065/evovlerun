/**
 * Inline SVG sparkline — no chart library needed. Renders a single
 * smoothed line for a CTL/ATL series. Tooltip support is intentionally
 * minimal; we keep the dashboard light.
 */
type Point = { x: number; y: number };

type Props = {
  data: (number | null)[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  ariaLabel?: string;
};

export function Sparkline({
  data,
  width = 280,
  height = 60,
  stroke = "currentColor",
  fill = "none",
  ariaLabel,
}: Props) {
  const clean = data
    .map((v, i) => (v == null ? null : { x: i, y: v }))
    .filter((p): p is Point => p !== null);
  if (clean.length < 2) {
    return (
      <div
        className="flex h-[60px] items-center justify-center text-xs text-neutral-400"
        style={{ width, height }}
      >
        Ikke nok data
      </div>
    );
  }

  const xs = clean.map((p) => p.x);
  const ys = clean.map((p) => p.y);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const yRange = yMax - yMin || 1;
  const xRange = xMax - xMin || 1;

  const padding = 4;
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  const path = clean
    .map((p, i) => {
      const x = padding + ((p.x - xMin) / xRange) * innerW;
      const y = padding + innerH - ((p.y - yMin) / yRange) * innerH;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  const last = clean[clean.length - 1];
  const lastX = padding + ((last.x - xMin) / xRange) * innerW;
  const lastY = padding + innerH - ((last.y - yMin) / yRange) * innerH;

  return (
    <svg
      width={width}
      height={height}
      role="img"
      aria-label={ariaLabel}
      className="overflow-visible"
    >
      <path d={path} fill={fill} stroke={stroke} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lastX} cy={lastY} r={2.5} fill={stroke} />
    </svg>
  );
}
