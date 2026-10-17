import en from "@/locales/en.json";
import hi from "@/locales/hi.json";
import pa from "@/locales/pa.json";

export type Dict = Record<string, string>;
/** Languages with a complete UI translation. Others (served by the backend for chat/results) show English chrome. */
export const UI_LANGS: Record<string, Dict> = { en: en as Dict, hi: hi as Dict, pa: pa as Dict };
export const FULL_UI = Object.keys(UI_LANGS);

export function translate(lang: string, key: string, fallback?: string, vars?: Record<string, string | number>): string {
  const s = UI_LANGS[lang]?.[key] ?? (en as Dict)[key] ?? fallback ?? key;
  return vars ? s.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`)) : s;
}
export type TFn = (key: string, fallback?: string, vars?: Record<string, string | number>) => string;
