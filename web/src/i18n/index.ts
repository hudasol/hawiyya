// English and Arabic. The Arabic copy is machine drafted by the author and needs review by a
// native speaker (stated on the Method screen).
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./ar.json";
import en from "./en.json";

export type Lang = "en" | "ar";

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ar: { translation: ar } },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function setLanguage(lang: Lang): void {
  void i18n.changeLanguage(lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
}

export default i18n;
