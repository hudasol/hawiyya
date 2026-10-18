// Design tokens: pearl and sakura, sketch brutalist. The single source for colours; applied
// as CSS custom properties at start up and checked for contrast by a test.
//
// The pastel accent (#d9728f) fails text contrast on pearl, so it is decorative only (hard
// shadows, highlights). Text, links and graphical marks use the darker derived tones.

export type ThemeName = "light" | "dark";

export interface Palette {
  bg: string; // page background
  surface: string; // cards
  highlight: string; // pastel highlight surface
  decor: string; // decorative accent (never text, never the only boundary)
  ink: string; // body text and 2 px borders
  muted: string; // secondary text
  strong: string; // links and graphical marks
  focus: string; // focus ring
  link: string; // decision LINK (recommend a merge request)
  review: string; // decision REVIEW
  apart: string; // decision KEEP_APART
}

export const PALETTES: Record<ThemeName, Palette> = {
  light: {
    bg: "#fdf8f5",
    surface: "#fbe3ea",
    highlight: "#f7b6c8",
    decor: "#d9728f",
    ink: "#5b3a4a",
    muted: "#7a4f61",
    strong: "#a3405e",
    focus: "#8a2e4c",
    link: "#2f6b4f",
    review: "#8a5a00",
    apart: "#4a4a6a",
  },
  dark: {
    bg: "#24151f",
    surface: "#33202c",
    highlight: "#4a2e3e",
    decor: "#c28aa3",
    ink: "#f8eaf0",
    muted: "#d9b6c6",
    strong: "#f3a6bf",
    focus: "#ffb8cf",
    link: "#8fd3b0",
    review: "#f2c46b",
    apart: "#b9b9e6",
  },
};

// Text pairs (foreground, background) that must reach 4.5:1, and graphical pairs that must
// reach 3:1 (WCAG 2.2 AA).
export const TEXT_PAIRS: [keyof Palette, keyof Palette][] = [
  ["ink", "bg"],
  ["ink", "surface"],
  ["ink", "highlight"],
  ["muted", "bg"],
  ["muted", "surface"],
  ["strong", "bg"],
  ["strong", "surface"],
  ["link", "bg"],
  ["link", "surface"],
  ["review", "bg"],
  ["review", "surface"],
  ["apart", "bg"],
  ["apart", "surface"],
];
export const GRAPHIC_PAIRS: [keyof Palette, keyof Palette][] = [
  ["ink", "bg"],
  ["strong", "bg"],
  ["strong", "surface"],
  ["focus", "bg"],
  ["focus", "surface"],
  ["link", "surface"],
  ["review", "surface"],
  ["apart", "surface"],
];

function channel(c: number): number {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

export function luminance(hex: string): number {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

export function applyTheme(name: ThemeName): void {
  const p = PALETTES[name];
  const root = document.documentElement;
  for (const [k, v] of Object.entries(p)) root.style.setProperty(`--${k}`, v);
  root.dataset.theme = name;
}
