"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { BadgeCheck, CalendarClock, ExternalLink, Landmark, RotateCcw } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import type { HaqQuestion, SchemeCard, TrackerItem } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/form-controls";
import { Alert, Skeleton } from "@/components/ui/misc";
import { ReadAloud, VoiceButton } from "@/components/voice";

const YES = /^(yes|y|haan|han|ha|हाँ|हां|हा|ਹਾਂ|ਹਾਂਜੀ)\b/i;
const NO = /^(no|n|nahi|nahin|नहीं|नही|ਨਹੀਂ|ਨਹੀ)\b/i;
const WORK_WORDS: Record<string, string[]> = { delivery: ["deliver", "डिलीवरी", "ਡਿਲੀਵਰੀ", "zomato", "swiggy"], driver: ["driver", "cab", "taxi", "ड्राइवर", "ਡਰਾਈਵਰ", "rickshaw", "auto"], domestic: ["domestic", "maid", "घरेलू", "ਘਰੇਲੂ"], construction: ["construction", "mason", "निर्माण", "ਉਸਾਰੀ", "mistri"], daily_wage: ["daily", "दिहाड़ी", "ਦਿਹਾੜੀ", "labour"], street_vendor: ["vendor", "रेहड़ी", "ਰੇਹੜੀ", "thela"] };

export function Haq() {
  const { t, lang, userId, refreshKey, refresh } = useApp();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [skipped, setSkipped] = useState<string[]>([]);
  const [questions, setQuestions] = useState<HaqQuestion[]>([]);
  const [cards, setCards] = useState<SchemeCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(false);
  const [input, setInput] = useState("");
  const [tracker, setTracker] = useState<Record<string, TrackerItem>>({});

  const evaluate = useCallback(async (a: Record<string, unknown>) => {
    setLoading(true); setErr(false);
    try { const r = await api.haqMatch(a, lang); setCards(r.cards); setQuestions(r.next_questions); } catch { setErr(true); } finally { setLoading(false); }
  }, [lang]);
  useEffect(() => { evaluate(answers); }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { api.tracked(userId).then((r) => setTracker(r.tracker)).catch(() => {}); }, [userId, refreshKey]);

  const pending = useMemo(() => questions.filter((q) => !skipped.includes(q.id)), [questions, skipped]);
  const q = pending[0];

  const answer = async (id: string, v: unknown) => { const a = { ...answers, [id]: v }; setAnswers(a); setInput(""); await evaluate(a); };
  const skip = (id: string) => { setSkipped([...skipped, id]); setInput(""); };
  const reset = () => { setAnswers({}); setSkipped([]); setInput(""); evaluate({}); };
  const fromVoice = (text: string) => {
    if (!q) return;
    if (q.type === "number") { const m = text.match(/\d+/); if (m) answer(q.id, Number(m[0])); else setInput(text); }
    else if (q.type === "bool") { if (YES.test(text.trim())) answer(q.id, true); else if (NO.test(text.trim())) answer(q.id, false); else setInput(text); }
    else if (q.type === "select" && q.options) { const low = text.toLowerCase(); const hit = q.options.find((o) => (WORK_WORDS[o] || []).some((w) => low.includes(w.toLowerCase())) || low.includes(o)); if (hit) answer(q.id, hit); else setInput(text); }
    else answer(q.id, text.trim().toLowerCase());
  };

  const save = async (id: string, extra: Record<string, unknown> = {}) => {
    const r = await api.track({ user: userId, scheme_id: id, ...extra });
    setTracker(r.tracker); refresh();
  };

  const order = ["potentially_relevant", "requires_official_confirmation", "more_info_needed", "appears_ineligible"] as const;
  const stateInfo = (s: SchemeCard["state"]) => ({
    potentially_relevant: { v: "default" as const, l: t("haq.s.rel", "Potentially relevant") },
    more_info_needed: { v: "warning" as const, l: t("haq.s.more", "More information needed") },
    appears_ineligible: { v: "outline" as const, l: t("haq.s.inel", "Appears ineligible based on supplied answers") },
    requires_official_confirmation: { v: "secondary" as const, l: t("haq.s.conf", "Eligibility requires official confirmation") },
  })[s];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="flex items-center justify-between gap-2"><span className="flex items-center gap-2"><Landmark className="size-4" />{t("haq.title", "HaqFinder - find schemes you may qualify for")}</span>
          <Button size="sm" variant="ghost" onClick={reset}><RotateCcw />{t("haq.reset", "Start over")}</Button></CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">{t("haq.intro", "Answer a few short questions. You can skip any question. We only ask what is needed - never your OTP, PIN or Aadhaar number.")}</p>
          {err && <Alert variant="error">{t("err.load", "Could not load. Please check your connection and try again.")}</Alert>}
          {q ? (
            <div className="space-y-2 rounded-xl bg-secondary p-3" aria-live="polite">
              <div className="flex items-start justify-between gap-2"><p className="text-lg font-semibold">{q.label}</p><ReadAloud text={q.label} /></div>
              {q.type === "bool" && <div className="flex gap-2"><Button onClick={() => answer(q.id, true)}>{t("common.yes", "Yes")}</Button><Button variant="outline" onClick={() => answer(q.id, false)}>{t("common.no", "No")}</Button></div>}
              {q.type === "select" && q.options && <div className="flex flex-wrap gap-2">{q.options.map((o) => <Button key={o} variant="outline" onClick={() => answer(q.id, o)}>{t(`work.${o}`, o)}</Button>)}</div>}
              {(q.type === "text" || q.type === "number") && (
                <form onSubmit={(e) => { e.preventDefault(); if (input.trim()) answer(q.id, q.type === "number" ? Number(input) : input.trim().toLowerCase()); }} className="flex items-start gap-2">
                  <label className="sr-only" htmlFor="haq-in">{q.label}</label>
                  <Input id="haq-in" type={q.type === "number" ? "number" : "text"} inputMode={q.type === "number" ? "numeric" : "text"} value={input} onChange={(e) => setInput(e.target.value)} />
                  <Button type="submit">{t("common.next", "Next")}</Button>
                </form>)}
              <div className="flex items-center gap-2"><VoiceButton onText={fromVoice} /><Button variant="ghost" size="sm" onClick={() => skip(q.id)}>{t("haq.skip", "Skip / not sure")}</Button></div>
            </div>
          ) : (!loading && <Alert variant="info">{t("haq.done", "That is all we need for now. See your results below.")}</Alert>)}
        </CardContent>
      </Card>

      {Object.keys(tracker).length > 0 && (
        <Card><CardHeader><CardTitle>{t("haq.tracker", "My applications")}</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
          {Object.values(tracker).map((tr) => (<div key={tr.scheme_id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-secondary p-2"><b>{tr.title}</b><span>{t(`track.${tr.status}`, tr.status)}{tr.reminder ? ` · ${t("haq.remind", "reminder")} ${tr.reminder}` : ""}</span></div>))}
          <p className="text-xs text-muted-foreground">{t("haq.track.note", "Status is recorded by you. GigSaathi does not submit applications on your behalf.")}</p></CardContent></Card>
      )}

      {loading && <Skeleton className="h-40" />}
      <div className="space-y-3">
        {order.flatMap((st) => cards.filter((c) => c.state === st)).map((c) => {
          const si = stateInfo(c.state); const tr = tracker[c.id];
          return (
            <Card key={c.id} className={c.state === "appears_ineligible" ? "opacity-80" : ""}>
              <CardHeader>
                <div className="flex flex-wrap items-center gap-2"><Badge variant={si.v}>{si.l}</Badge>
                  <Badge variant={c.verification === "verified" ? "default" : "warning"}>{c.verification === "verified" ? <><BadgeCheck className="size-3" />{t("src.verified", "verified")} {c.last_verified}</> : t("src.unverified2", "Not yet verified - confirm on the official portal")}</Badge>
                  {c.text_language !== lang && lang !== "en" && <Badge variant="outline">{t("haq.en", "Text in English")}</Badge>}</div>
                <CardTitle>{c.title}</CardTitle><p className="text-xs text-muted-foreground">{c.authority}</p>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{c.summary}</p>
                {c.why_qualify.length > 0 && <div><p className="font-semibold">{t("haq.why", "Why you may qualify")}</p><ul className="ml-4 list-disc">{c.why_qualify.map((w) => <li key={w}>{w}</li>)}</ul></div>}
                {c.why_not.length > 0 && <div><p className="font-semibold text-destructive">{t("haq.whynot", "Why it may not apply")}</p><ul className="ml-4 list-disc">{c.why_not.map((w) => <li key={w}>{w}</li>)}</ul></div>}
                {c.missing.length > 0 && <p className="rounded-lg bg-warning p-2 text-warning-foreground">{t("haq.missing", "Still needed to check:")} {c.missing.map((m) => t(`q.${m}`, m)).join(", ")}</p>}
                <details><summary className="cursor-pointer font-semibold">{t("haq.details", "Benefits, exclusions, documents and steps")}</summary>
                  <div className="mt-2 space-y-2">
                    {c.benefits.length > 0 && <div><b>{t("haq.benefits", "Benefits")}</b><ul className="ml-4 list-disc">{c.benefits.map((b) => <li key={b}>{b}</li>)}</ul></div>}
                    {c.exclusions.length > 0 && <div><b>{t("haq.excl", "Exclusions")}</b><ul className="ml-4 list-disc">{c.exclusions.map((b) => <li key={b}>{b}</li>)}</ul></div>}
                    {c.documents.length > 0 && <div><b>{t("haq.docs", "Documents needed")}</b><ul className="ml-4 list-disc">{c.documents.map((b) => <li key={b}>{b}</li>)}</ul></div>}
                    {c.steps.length > 0 && <div><b>{t("haq.steps", "Application steps")}</b><ol className="ml-4 list-decimal">{c.steps.map((b) => <li key={b}>{b}</li>)}</ol></div>}
                    <p>{c.how_to_apply}</p>
                    {c.channels.length > 0 && <p><b>{t("haq.help", "Where to get help")}:</b> {c.channels.join(" · ")}</p>}
                  </div></details>
                <div><p className="font-semibold">{t("haq.sources", "Sources")}</p><ul className="ml-4 list-disc text-xs">{c.sources.map((s) => <li key={s.url}><a className="text-primary underline" href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a> - {s.authority} · {s.last_verified ? `${t("src.verified", "verified")} ${s.last_verified}` : t("src.unverified", "not yet verified")}</li>)}</ul></div>
                <p className="text-xs text-muted-foreground">{t("haq.disclaimer", "This is a first check against published rules, not a decision. Only the official authority can confirm eligibility.")}</p>
                <div className="flex flex-wrap items-center gap-2">
                  <Button asChild size="sm"><a href={c.apply_url} target="_blank" rel="noopener noreferrer"><ExternalLink />{t("haq.apply", "Official application link")}</a></Button>
                  {c.state !== "appears_ineligible" && !tr && <Button size="sm" variant="outline" onClick={() => save(c.id)}>{t("haq.save", "Save to my list")}</Button>}
                </div>
                {tr && (
                  <div className="space-y-2 rounded-lg bg-secondary p-3">
                    <div className="grid gap-2 sm:grid-cols-2">
                      <Field id={`st-${c.id}`} label={t("haq.status", "My status (recorded by me)")}><Select id={`st-${c.id}`} value={tr.status} onChange={(e) => save(c.id, { status: e.target.value })}>
                        {["saved", "documents_ready", "applied", "received", "rejected"].map((s) => <option key={s} value={s}>{t(`track.${s}`, s)}</option>)}</Select></Field>
                      <Field id={`rm-${c.id}`} label={t("haq.reminder", "Reminder date")}><div className="flex items-center gap-1"><CalendarClock className="size-4" /><Input id={`rm-${c.id}`} type="date" value={tr.reminder || ""} onChange={(e) => e.target.value && save(c.id, { reminder: e.target.value })} /></div></Field>
                    </div>
                    <div><p className="font-semibold">{t("haq.checklist", "Document checklist")}</p>
                      {Object.entries(tr.checklist).map(([d, done]) => <label key={d} className="flex items-center gap-2 py-1"><input type="checkbox" className="size-5" checked={done} onChange={(e) => save(c.id, { checklist: { [d]: e.target.checked } })} />{d}</label>)}</div>
                  </div>)}
              </CardContent>
            </Card>);
        })}
      </div>
    </div>
  );
}
