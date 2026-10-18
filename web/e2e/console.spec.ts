// End to end checks on the static build. Requirement ids: HW-L9-001, HW-L9-006, HW-L9-010,
// HW-L9-004, HW-L9-003. Screenshots are written to docs/img for design review.
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const IMG = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "docs", "img");

const SCREENS = [
  { path: "/#/", name: "overview" },
  { path: "/#/check", name: "check" },
  { path: "/#/names", name: "names" },
];

async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("status")).toHaveCount(0, { timeout: 15_000 });
}

for (const s of SCREENS) {
  test(`${s.name}: banner, axe and screenshot (HW-L9-001 HW-L9-006)`, async ({ page }) => {
    await page.goto(s.path);
    await settle(page);
    await expect(page.getByTestId("synthetic-banner")).toBeVisible();
    const axe = await new AxeBuilder({ page }).analyze();
    expect(axe.violations.map((v) => v.id)).toEqual([]);
    await page.screenshot({ path: `${IMG}/${s.name}-en-light-1440.png`, fullPage: true });
  });

  test(`${s.name}: Arabic right to left (HW-L9-003)`, async ({ page }) => {
    await page.goto(s.path);
    await settle(page);
    // Arabic strings as escapes: the word for Arabic, and the word for synthetic (plural).
    await page.getByRole("button", { name: "العربية" }).click();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.getByTestId("synthetic-banner")).toContainText(
      "اصطناعيون",
    );
    const axe = await new AxeBuilder({ page }).analyze();
    expect(axe.violations.map((v) => v.id)).toEqual([]);
    await page.screenshot({ path: `${IMG}/${s.name}-ar-light-1440.png`, fullPage: true });
  });
}

test("registration check controls are at least 44 pixels (HW-L9-010)", async ({ page }) => {
  await page.goto("/#/check");
  await settle(page);
  const controls = page.locator(
    "main button:visible, main select:visible, main input:visible, main summary:visible",
  );
  const n = await controls.count();
  expect(n).toBeGreaterThan(0);
  for (let i = 0; i < n; i++) {
    const box = await controls.nth(i).boundingBox();
    if (box) expect(box.height).toBeGreaterThanOrEqual(44);
  }
});

test("every rendered name is bidi isolated (HW-L9-004)", async ({ page }) => {
  await page.goto("/#/check");
  await settle(page);
  const names = page.getByTestId("name");
  const n = await names.count();
  expect(n).toBeGreaterThan(0);
  for (let i = 0; i < n; i++) {
    expect(await names.nth(i).evaluate((el) => el.tagName)).toBe("BDI");
  }
});
