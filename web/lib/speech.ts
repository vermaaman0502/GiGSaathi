/**
 * Speech provider abstraction. The UI only talks to `SpeechProvider`, so Bhashini/Sarvam can replace the
 * browser engine without touching components. Only the browser provider is implemented; the others are
 * stubs that report themselves as unavailable (they need a server-side proxy and API keys - see README).
 */
export interface SpeechProvider {
  id: string;
  label: string;
  canListen(): boolean;
  canSpeak(): boolean;
  /** Start recording; resolves transcript through onResult. Returns a stop() function. */
  listen(lang: string, onResult: (text: string) => void, onError: (reason: string) => void): () => void;
  speak(text: string, lang: string): void;
  stopSpeaking(): void;
}

type SR = { lang: string; interimResults: boolean; onresult: (e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void; onerror: (e: { error: string }) => void; onend: () => void; start(): void; stop(): void };
type SRCtor = new () => SR;
const getSR = (): SRCtor | null => {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: SRCtor; webkitSpeechRecognition?: SRCtor };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
};

export const SPEECH_TAGS: Record<string, string> = {
  en: "en-IN", hi: "hi-IN", hinglish: "hi-IN", pa: "pa-IN", bn: "bn-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN", gu: "gu-IN", kn: "kn-IN", ml: "ml-IN", or: "or-IN", ur: "ur-IN",
};

export const browserProvider: SpeechProvider = {
  id: "browser", label: "Browser speech",
  canListen: () => !!getSR(),
  canSpeak: () => typeof window !== "undefined" && "speechSynthesis" in window,
  listen(lang, onResult, onError) {
    const Ctor = getSR();
    if (!Ctor) { onError("unsupported"); return () => {}; }
    const r = new Ctor();
    r.lang = SPEECH_TAGS[lang] || "en-IN";
    r.interimResults = false;
    r.onresult = (e) => onResult(e.results[0][0].transcript);
    r.onerror = (e) => onError(e.error || "error");
    r.onend = () => {};
    try { r.start(); } catch { onError("error"); }
    return () => { try { r.stop(); } catch { /* already stopped */ } };
  },
  speak(text, lang) {
    if (!this.canSpeak() || !text) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = SPEECH_TAGS[lang] || "en-IN";
    window.speechSynthesis.speak(u);
  },
  stopSpeaking() { if (this.canSpeak()) window.speechSynthesis.cancel(); },
};

const unavailable = (id: string, label: string): SpeechProvider => ({
  id, label: `${label} (not configured)`, canListen: () => false, canSpeak: () => false,
  listen: (_l, _r, onError) => { onError("not_configured"); return () => {}; }, speak: () => {}, stopSpeaking: () => {},
});

export const providers: Record<string, SpeechProvider> = {
  browser: browserProvider,
  bhashini: unavailable("bhashini", "Bhashini"),
  sarvam: unavailable("sarvam", "Sarvam"),
};

export function getSpeech(): SpeechProvider {
  const wanted = process.env.NEXT_PUBLIC_SPEECH_PROVIDER || "browser";
  const p = providers[wanted] || browserProvider;
  return p.canListen() || p.canSpeak() ? p : browserProvider;     // fall back instead of breaking the UI
}
