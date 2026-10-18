// Component tests. Requirement ids: HW-L9-001 (banner), HW-L9-004 (bidi isolation),
// HW-L9-005 (contrast), HW-L9-009 (decision shapes), HW-L9-010 (touch targets in CSS).
import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { GRAPHIC_PAIRS, PALETTES, TEXT_PAIRS, contrast } from "../theme/tokens";
import { DecisionBadge, Ident, Name, SyntheticBanner } from "./Basics";

describe("HW-L9-001 synthetic banner", () => {
  it("states the synthetic data rule and cannot be dismissed", () => {
    render(<SyntheticBanner />);
    const b = screen.getByTestId("synthetic-banner");
    expect(b).toHaveTextContent(
      "All patients in this demonstration are synthetic. Identifiers are synthetic and belong to no person.",
    );
    expect(b.querySelector("button")).toBeNull();
  });
});

describe("HW-L9-004 bidi isolation", () => {
  it("renders names inside an isolating bdi element", () => {
    render(
      <>
        <Name value="محمد Ali 7amad (2)" />
        <Ident value="784199012345671" />
      </>,
    );
    const els = screen.getAllByTestId("name");
    expect(els).toHaveLength(2);
    for (const el of els) {
      expect(el.tagName).toBe("BDI");
      expect(el.getAttribute("dir")).toMatch(/auto|ltr/);
    }
  });
});

describe("HW-L9-005 contrast", () => {
  for (const theme of ["light", "dark"] as const) {
    it(`text pairs reach 4.5:1 and graphics 3:1 in the ${theme} theme`, () => {
      const p = PALETTES[theme];
      for (const [fg, bg] of TEXT_PAIRS) expect(contrast(p[fg], p[bg])).toBeGreaterThanOrEqual(4.5);
      for (const [fg, bg] of GRAPHIC_PAIRS) expect(contrast(p[fg], p[bg])).toBeGreaterThanOrEqual(3);
    });
  }
  it("documents that the pastel accent fails text contrast and is decorative only", () => {
    expect(contrast(PALETTES.light.decor, PALETTES.light.bg)).toBeLessThan(4.5);
  });
});

describe("HW-L9-009 decisions encoded by shape and label", () => {
  it("uses a distinct shape and a text label for each decision", () => {
    const shapes = new Set<string>();
    for (const k of ["LINK", "REVIEW", "KEEP_APART"] as const) {
      const { container, unmount } = render(<DecisionBadge kind={k} />);
      const svg = container.querySelector("svg");
      expect(svg?.getAttribute("aria-hidden")).toBe("true");
      shapes.add(svg?.firstElementChild?.tagName ?? "");
      expect(container.textContent?.length).toBeGreaterThan(3);
      unmount();
    }
    expect(shapes.size).toBe(3);
  });
});

describe("HW-L9-010 touch targets", () => {
  it("sets a 44 pixel minimum on buttons and inputs", () => {
    const css = readFileSync(resolve(__dirname, "../theme/global.css"), "utf-8");
    const button = css.slice(css.indexOf("button,"), css.indexOf("button.primary"));
    const input = css.slice(css.indexOf("input,"), css.indexOf("label {"));
    expect(button).toContain("min-height: 44px");
    expect(input).toContain("min-height: 44px");
  });
});
