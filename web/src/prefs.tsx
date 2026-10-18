// Viewer preferences: language, digit style and theme. Number and time formatting helpers.
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { setLanguage, type Lang } from "./i18n";
import { applyTheme, type ThemeName } from "./theme/tokens";

export interface Prefs {
  lang: Lang;
  arabicDigits: boolean;
  theme: ThemeName;
  setLang: (l: Lang) => void;
  setArabicDigits: (v: boolean) => void;
  setTheme: (t: ThemeName) => void;
}

const PrefsContext = createContext<Prefs | null>(null);

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [arabicDigits, setArabicDigits] = useState(false);
  const [theme, setThemeState] = useState<ThemeName>("light");
  const value = useMemo<Prefs>(
    () => ({
      lang,
      arabicDigits,
      theme,
      setLang: (l) => {
        setLanguage(l);
        setLangState(l);
      },
      setArabicDigits,
      setTheme: (t) => {
        applyTheme(t);
        setThemeState(t);
      },
    }),
    [lang, arabicDigits, theme],
  );
  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
}

export function usePrefs(): Prefs {
  const p = useContext(PrefsContext);
  if (!p) throw new Error("PrefsProvider missing");
  return p;
}

export function formatNumber(
  value: number,
  arabicDigits: boolean,
  opts: Intl.NumberFormatOptions = {},
): string {
  const locale = arabicDigits ? "ar-u-nu-arab" : "en-u-nu-latn";
  return new Intl.NumberFormat(locale, opts).format(value);
}

export function useFormat() {
  const { arabicDigits } = usePrefs();
  return {
    num: (v: number, digits = 0) =>
      formatNumber(v, arabicDigits, { maximumFractionDigits: digits, minimumFractionDigits: digits }),
    pct: (v: number, digits = 1) =>
      formatNumber(v, arabicDigits, {
        style: "percent",
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      }),
    time: (iso: string) =>
      new Intl.DateTimeFormat(arabicDigits ? "ar-u-nu-arab" : "en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Asia/Dubai",
      }).format(new Date(iso)),
  };
}
