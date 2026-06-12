// Generates public/og.png (1200x630) from an inline SVG using sharp.
// Run from frontend/: node scripts/generate-og.mjs
import sharp from "sharp";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

// Brand tokens from app/_landing/landing.css
const BG = "#f3ede3";
const INK = "#1a1612";
const INK2 = "#5c544a";
const INK3 = "#8a8074";

const svg = `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="20%">
      <stop offset="0%" stop-color="#ff6b46"/>
      <stop offset="48%" stop-color="#e0517a"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
    <radialGradient id="bloom" cx="50%" cy="0%" r="80%">
      <stop offset="0%" stop-color="#ff6b46" stop-opacity="0.14"/>
      <stop offset="55%" stop-color="#e0517a" stop-opacity="0.07"/>
      <stop offset="100%" stop-color="#a855f7" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="630" fill="${BG}"/>
  <rect width="1200" height="630" fill="url(#bloom)"/>

  <!-- wordmark (pulse mark composited separately from evr-logo.png) -->
  <text x="148" y="116" font-family="Iowan Old Style, Georgia, serif" font-size="34" font-weight="600" fill="${INK}">EvolveRun</text>

  <!-- headline -->
  <text x="100" y="320" font-family="Iowan Old Style, Georgia, serif" font-size="92" font-weight="500" letter-spacing="-2" fill="${INK}">Understand your</text>
  <text x="100" y="424" font-family="Iowan Old Style, Georgia, serif" font-size="92" font-weight="500" letter-spacing="-2" fill="url(#grad)">training with AI.</text>

  <!-- sub-line -->
  <text x="102" y="510" font-family="Helvetica, Arial, sans-serif" font-size="28" fill="${INK2}">Connect Strava to Claude &amp; ChatGPT — real answers from your real data.</text>

  <!-- footer rule + tag -->
  <line x1="100" y1="560" x2="1100" y2="560" stroke="${INK}" stroke-opacity="0.1" stroke-width="1"/>
  <text x="100" y="596" font-family="Menlo, monospace" font-size="17" letter-spacing="3" fill="${INK3}">BUILT FOR RUNNERS WHO WANT THE TRUTH</text>
</svg>`;

const logo = await sharp(path.join(root, "public/evr-logo.png"))
  .resize(44, 44)
  .png()
  .toBuffer();

await sharp(Buffer.from(svg))
  .composite([{ input: logo, top: 84, left: 96 }])
  .png()
  .toFile(path.join(root, "public/og.png"));

console.log("wrote public/og.png");
