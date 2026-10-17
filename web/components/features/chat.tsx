"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Send, WifiOff } from "lucide-react";
import { useApp } from "@/app/providers";
import { api, ApiError } from "@/lib/api";
import { getSpeech } from "@/lib/speech";
import { safeGet, safeSet } from "@/lib/user";
import type { ChatReply } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/form-controls";
import { Alert } from "@/components/ui/misc";
import { ReadAloud, VoiceButton } from "@/components/voice";

interface Msg { role: "user" | "bot"; text: string; reply?: ChatReply; pending?: boolean }
const OUTBOX = "gs_outbox";

export function Chat() {
  const { t, userId, lang } = useApp();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [online, setOnline] = useState(true);
  const qs = useSearchParams();
  const bottom = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  const send = useCallback(async (q: string, fromOutbox = false) => {
    if (!q.trim()) return;
    if (!fromOutbox) setMsgs((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const r = await api.chat(userId, q, lang);
      setMsgs((m) => [...m.filter((x) => !(x.pending && x.text.startsWith(q))), { role: "bot", text: r.reply, reply: r }]);
      getSpeech().speak(r.reply, r.lang);                       // spoken in the language the worker wrote in
    } catch (e) {
      if (e instanceof ApiError && e.status === 0) {          // offline: keep the draft and retry later
        const box: string[] = JSON.parse(safeGet(OUTBOX) || "[]");
        if (!box.includes(q)) { box.push(q); safeSet(OUTBOX, JSON.stringify(box)); }
        setMsgs((m) => [...m, { role: "bot", pending: true, text: q + " — " + t("chat.queued", "saved on this phone. It will be sent when you are online.") }]);
      } else setMsgs((m) => [...m, { role: "bot", text: t("err.chat", "Sorry, something went wrong. Please try again.") }]);
    } finally { setBusy(false); }
  }, [userId, lang, t]);

  useEffect(() => {
    const flush = async () => {
      setOnline(true);
      const box: string[] = JSON.parse(safeGet(OUTBOX) || "[]");
      if (box.length) { safeSet(OUTBOX, "[]"); for (const q of box) await send(q, true); }
    };
    const off = () => setOnline(false);
    setOnline(navigator.onLine);
    window.addEventListener("online", flush); window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", flush); window.removeEventListener("offline", off); };
  }, [send]);

  useEffect(() => { const q = qs.get("q"); if (q && !started.current && userId) { started.current = true; send(q); } }, [qs, send, userId]);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const chips = [t("chat.c1", "Which schemes can I get?"), t("chat.c2", "trip fare 120 distance 8 km"), t("chat.c3", "aaj 850 kamaye"), t("chat.c4", "loan 10000 emi 1200 for 12 months")];
  return (
    <div className="flex h-[calc(100vh-14rem)] min-h-96 flex-col gap-3 md:h-[calc(100vh-10rem)]">
      {!online && <Alert variant="warning"><WifiOff className="mr-1 inline size-4" />{t("chat.offline", "You are offline. Messages are saved on your phone and sent when you reconnect.")}</Alert>}
      <p className="text-xs text-muted-foreground">{t("chat.lang.note", "Ask in any language - Saathi answers in the language you write or speak in. Never share your OTP, PIN, password or full Aadhaar number.")}</p>
      <Card className="flex-1 space-y-3 overflow-y-auto p-3" role="log" aria-live="polite" aria-label={t("nav.saathi", "Saathi AI")}>
        {msgs.length === 0 && (
          <div className="space-y-2"><p className="text-sm text-muted-foreground">{t("chat.empty", "Say or type a question. For example:")}</p>
            <div className="flex flex-wrap gap-2">{chips.map((c) => <button key={c} onClick={() => send(c)} className="rounded-full border border-primary px-3 py-1.5 text-sm font-medium text-primary hover:bg-accent">{c}</button>)}</div></div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "ml-auto max-w-[85%] rounded-2xl bg-primary px-3 py-2 text-primary-foreground" : "max-w-[90%] rounded-2xl bg-secondary px-3 py-2"}>
            <p className="whitespace-pre-wrap">{m.text}</p>
            {m.reply && m.reply.escalate && <p className="mt-1 text-xs font-semibold text-destructive">{t("chat.escalate", "This looks serious. Please call 112 now - a human can help.")} <a className="underline" href="tel:112">112</a></p>}
            {m.reply && m.reply.sources.length > 0 && <ul className="mt-1 space-y-0.5 text-xs">{m.reply.sources.map((s) => <li key={s.url}><a className="underline" href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a> · {s.last_verified ? `${t("src.verified", "verified")} ${s.last_verified}` : t("src.unverified", "not yet verified")}</li>)}</ul>}
            {m.role === "bot" && !m.pending && <ReadAloud text={m.text} />}
          </div>
        ))}
        {busy && <div className="skeleton h-10 w-40" aria-label={t("chat.thinking", "Thinking")} />}
        <div ref={bottom} />
      </Card>
      <form onSubmit={(e) => { e.preventDefault(); const q = text; setText(""); send(q); }} className="flex items-start gap-2">
        <label htmlFor="chat-in" className="sr-only">{t("ui.ph", "Type or speak your question")}</label>
        <Input id="chat-in" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("ui.ph", "Type or speak your question")} autoComplete="off" />
        <VoiceButton onText={(v) => send(v)} />
        <Button type="submit" size="icon" aria-label={t("ui.send", "Send")} disabled={busy}><Send /></Button>
      </form>
    </div>
  );
}
