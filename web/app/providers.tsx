"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { translate, type TFn } from "@/lib/i18n";
import { newToken, safeGet, safeSet } from "@/lib/user";

type Mode = "real" | "demo";
interface Ctx {
  lang: string; setLang: (l: string) => void; t: TFn;
  userId: string; mode: Mode; setMode: (m: Mode) => Promise<void>; ready: boolean;
  textSize: string; setTextSize: (s: string) => void; contrast: boolean; setContrast: (b: boolean) => void; dark: boolean; setDark: (b: boolean) => void;
  consent: { voice: boolean; location: boolean }; setConsent: (k: "voice" | "location", v: boolean) => void;
  refreshKey: number; refresh: () => void;
}
const AppCtx = createContext<Ctx | null>(null);
export const useApp = () => {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp outside provider");
  return c;
};

export function Providers({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState("en");
  const [realId, setRealId] = useState("");
  const [demoId, setDemoId] = useState("");
  const [mode, setModeState] = useState<Mode>("real");
  const [ready, setReady] = useState(false);
  const [textSize, setTextSizeS] = useState("normal");
  const [contrast, setContrastS] = useState(false);
  const [dark, setDarkS] = useState(false);
  const [consent, setConsentS] = useState({ voice: false, location: false });
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const qs = new URLSearchParams(location.search);
    let rid = safeGet("gs_user"); if (!rid) { rid = newToken("u-"); safeSet("gs_user", rid); }
    let did = safeGet("gs_demo"); if (!did) { did = newToken("demo-").slice(0, 21); safeSet("gs_demo", did); }
    setRealId(rid); setDemoId(did);
    setLangState(qs.get("lang") || safeGet("gs_lang") || (navigator.language || "en").slice(0, 2));
    setModeState(((qs.get("mode") as Mode) || (safeGet("gs_mode") as Mode) || "real") === "demo" ? "demo" : "real");
    setTextSizeS(safeGet("gs_text") || "normal"); setContrastS(safeGet("gs_contrast") === "1");
    setDarkS(safeGet("gs_dark") ? safeGet("gs_dark") === "1" : window.matchMedia?.("(prefers-color-scheme: dark)").matches);
    setConsentS({ voice: safeGet("gs_c_voice") === "1", location: safeGet("gs_c_loc") === "1" });
    setReady(true);
  }, []);

  useEffect(() => {
    const h = document.documentElement;
    h.lang = lang; h.dataset.text = textSize; h.dataset.contrast = contrast ? "high" : "normal"; h.classList.toggle("dark", dark);
  }, [lang, textSize, contrast, dark]);

  // make sure the demo workspace exists when demo mode is active (idempotent on the server)
  useEffect(() => {
    if (ready && mode === "demo" && demoId && !safeGet("gs_demo_seeded")) {
      api.seedDemo(demoId).then(() => { safeSet("gs_demo_seeded", "1"); setRefreshKey((k) => k + 1); }).catch(() => {});
    }
  }, [ready, mode, demoId]);

  const setLang = useCallback((l: string) => { setLangState(l); safeSet("gs_lang", l); }, []);
  const setMode = useCallback(async (m: Mode) => {
    if (m === "demo") { await api.seedDemo(demoId).then(() => safeSet("gs_demo_seeded", "1")).catch(() => {}); }
    setModeState(m); safeSet("gs_mode", m); setRefreshKey((k) => k + 1);
  }, [demoId]);
  const t: TFn = useCallback((key, fallback, vars) => translate(lang, key, fallback, vars), [lang]);

  const value = useMemo<Ctx>(() => ({
    lang, setLang, t, userId: mode === "demo" ? demoId : realId, mode, setMode, ready,
    textSize, setTextSize: (s) => { setTextSizeS(s); safeSet("gs_text", s); },
    contrast, setContrast: (b) => { setContrastS(b); safeSet("gs_contrast", b ? "1" : "0"); },
    dark, setDark: (b) => { setDarkS(b); safeSet("gs_dark", b ? "1" : "0"); },
    consent, setConsent: (k, v) => { setConsentS((c) => ({ ...c, [k]: v })); safeSet(k === "voice" ? "gs_c_voice" : "gs_c_loc", v ? "1" : "0"); },
    refreshKey, refresh: () => setRefreshKey((k) => k + 1),
  }), [lang, setLang, t, mode, demoId, realId, setMode, ready, textSize, contrast, dark, consent, refreshKey]);

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
