/**
 * Decode a Google "encoded polyline" string into [lat, lng] pairs.
 * Strava stores route geometry as `map.summary_polyline` in this format.
 * Algorithm: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
 */
export function decodePolyline(encoded: string): [number, number][] {
  const points: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let result = 0;
    let shift = 0;
    let byte: number;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lat += result & 1 ? ~(result >> 1) : result >> 1;

    result = 0;
    shift = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lng += result & 1 ? ~(result >> 1) : result >> 1;

    points.push([lat / 1e5, lng / 1e5]);
  }

  return points;
}

/**
 * Project decoded [lat, lng] points into an SVG path `d` string that fits a
 * `width × height` viewBox, preserving aspect ratio. Returns null if there's
 * nothing to draw. Latitude is flipped so north is up.
 */
export function polylineToSvgPath(
  points: [number, number][],
  width: number,
  height: number,
  pad = 6,
): string | null {
  if (points.length < 2) return null;

  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;
  for (const [lat, lng] of points) {
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
  }

  // Correct longitude for latitude so the trace isn't horizontally stretched.
  const latRange = Math.max(maxLat - minLat, 1e-6);
  const lngScale = Math.cos(((minLat + maxLat) / 2) * (Math.PI / 180));
  const lngRange = Math.max((maxLng - minLng) * lngScale, 1e-6);

  const innerW = width - pad * 2;
  const innerH = height - pad * 2;
  const scale = Math.min(innerW / lngRange, innerH / latRange);
  const offsetX = pad + (innerW - lngRange * scale) / 2;
  const offsetY = pad + (innerH - latRange * scale) / 2;

  return points
    .map(([lat, lng], i) => {
      const x = offsetX + (lng - minLng) * lngScale * scale;
      const y = offsetY + (maxLat - lat) * scale; // flip: north up
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}
