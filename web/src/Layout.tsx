import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MODE } from "./api";
import { SyntheticBanner } from "./components/Basics";
import { usePrefs } from "./prefs";

export const ROUTES: { path: string; key: string }[] = [
  { path: "/", key: "overview" },
  { path: "/check", key: "check" },
  { path: "/review", key: "review" },
  { path: "/clusters", key: "clusters" },
  { path: "/placeholders", key: "placeholders" },
  { path: "/names", key: "names" },
  { path: "/thresholds", key: "thresholds" },
  { path: "/equity", key: "equity" },
  { path: "/experiments", key: "experiments" },
  { path: "/method", key: "method" },
  { path: "/audit", key: "audit" },
];

export function Layout({ available }: { available: Set<string> }) {
  const { t } = useTranslation();
  const p = usePrefs();
  return (
    <>
      <header>
        <SyntheticBanner />
      </header>
      <div className="shell">
        <nav className="nav" aria-label="Main">
          <h1 style={{ fontSize: "1.6rem", marginBlockEnd: 0 }}>{t("app.title")}</h1>
          <p className="muted" style={{ marginBlockStart: 0 }}>
            {t("app.subtitle")}
          </p>
          <ul>
            {ROUTES.filter((r) => available.has(r.key)).map((r) => (
              <li key={r.key}>
                <NavLink to={r.path} end={r.path === "/"}>
                  {t(`nav.${r.key}`)}
                </NavLink>
              </li>
            ))}
          </ul>
          <div className="toolbar" style={{ marginBlockStart: "1rem" }}>
            <button
              type="button"
              lang={p.lang === "en" ? "ar" : "en"}
              onClick={() => p.setLang(p.lang === "en" ? "ar" : "en")}
            >
              {t("app.language")}
            </button>
            <button
              type="button"
              aria-pressed={p.arabicDigits}
              onClick={() => p.setArabicDigits(!p.arabicDigits)}
            >
              {p.arabicDigits ? t("app.digits_latin") : t("app.digits_arabic")}
            </button>
            <button
              type="button"
              aria-pressed={p.theme === "dark"}
              onClick={() => p.setTheme(p.theme === "light" ? "dark" : "light")}
            >
              {p.theme === "light" ? t("app.theme_dark") : t("app.theme_light")}
            </button>
          </div>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {MODE === "static" ? t("app.mode_static") : t("app.mode_live")}
          </p>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {t("app.advisory")}
          </p>
        </nav>
        <main className="main" id="main">
          <Outlet />
        </main>
      </div>
    </>
  );
}
