"use client";
import { useRef, useState } from "react";
import { Mic, MicOff, Square, Volume2 } from "lucide-react";
import { useApp } from "@/app/providers";
import { getSpeech } from "@/lib/speech";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/misc";

/** Mic button. Asks for consent before the first recording; falls back to typing whenever speech fails. */
export function VoiceButton({ onText, size = "icon", label }: { onText: (text: string) => void; size?: "icon" | "lg"; label?: string }) {
  const { lang, t, consent, setConsent } = useApp();
  const [listening, setListening] = useState(false);
  const [asking, setAsking] = useState(false);
  const [err, setErr] = useState("");
  const stop = useRef<() => void>(() => {});
  const sp = getSpeech();

  const start = () => {
    setErr("");
    if (!sp.canListen()) { setErr(t("voice.unsupported", "Voice input is not available on this device. Please type instead.")); return; }
    setListening(true);
    stop.current = sp.listen(lang, (txt) => { setListening(false); onText(txt); }, (reason) => {
      setListening(false);
      setErr(reason === "not-allowed" ? t("voice.denied", "Microphone permission was denied. You can type instead.") : t("voice.failed", "Could not hear you. Please try again or type."));
    });
  };
  const click = () => { if (listening) { stop.current(); setListening(false); } else if (!consent.voice) setAsking(true); else start(); };

  return (
    <div>
      <Button type="button" size={size} variant={listening ? "destructive" : size === "lg" ? "default" : "outline"} onClick={click} aria-pressed={listening}
        aria-label={listening ? t("voice.stop", "Stop") : t("voice.start", "Speak")} className={size === "lg" ? "w-full" : ""}>
        {listening ? <Square /> : sp.canListen() ? <Mic /> : <MicOff />}{size === "lg" && (label || (listening ? t("voice.listening", "Listening…") : t("voice.talk", "Talk to Saathi")))}
      </Button>
      {asking && (
        <Alert variant="warning" className="mt-2" title={t("voice.consent.title", "Allow voice input?")}>
          <p>{t("voice.consent.body", "Your phone or browser will record your voice to turn it into text. We do not store the recording.")}</p>
          <div className="mt-2 flex gap-2">
            <Button size="sm" onClick={() => { setConsent("voice", true); setAsking(false); start(); }}>{t("common.allow", "Allow")}</Button>
            <Button size="sm" variant="outline" onClick={() => setAsking(false)}>{t("common.notnow", "Not now")}</Button>
          </div>
        </Alert>
      )}
      {err && <p role="alert" className="mt-1 text-xs text-destructive">{err}</p>}
    </div>
  );
}

export function ReadAloud({ text }: { text: string }) {
  const { lang, t } = useApp();
  const sp = getSpeech();
  if (!sp.canSpeak() || !text) return null;
  return (
    <Button type="button" size="sm" variant="ghost" onClick={() => sp.speak(text, lang)} aria-label={t("voice.read", "Read aloud")}>
      <Volume2 />{t("voice.read", "Read aloud")}
    </Button>
  );
}
