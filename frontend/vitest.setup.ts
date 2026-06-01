// Runs before every test file. Adds jest-dom matchers (toBeInTheDocument,
// toHaveTextContent, …) to Vitest's expect.
import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// jsdom lacks these browser APIs that framer-motion relies on
// (useReducedMotion → matchMedia, useInView → IntersectionObserver).
// Polyfill them so motion-wrapped components render in tests.
if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

if (!("IntersectionObserver" in window)) {
  class MockIntersectionObserver {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
    takeRecords = vi.fn(() => []);
    root = null;
    rootMargin = "";
    thresholds = [];
  }
  vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);
}
