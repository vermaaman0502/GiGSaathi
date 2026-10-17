"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Download, MessageSquareWarning, PenLine } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { grievanceSchema, toNum, type GrievanceForm } from "@/lib/schemas";
import type { Grievance } from "@/lib/types";
import { useAsync } from "@/lib/use-async";
import { today } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/form-controls";
import { Alert } from "@/components/ui/misc";
import { VoiceButton } from "@/components/voice";

const STATUSES: Grievance["status"][] = ["draft", "ready", "submitted", "resolved"];

export function GrievanceBuilder() {
  const { t, lang, userId, refreshKey, refresh } = useApp();
  const list = useAsync(() => api.grievances(userId), [userId, refreshKey]);
  const [sel, setSel] = useState<Grievance | null>(null);
  const [letter, setLetter] = useState("");
  const [evLines, setEvLines] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const form = useForm<GrievanceForm>({ resolver: zodResolver(grievanceSchema), defaultValues: { issue: "deduction", name: "", company: "", incident_date: today(), amount: 0, details: "", desired: "" } });
  const e = form.formState.errors;

  useEffect(() => { if (sel) setLetter(sel.letter); }, [sel]);
  useEffect(() => { if (sel && list.data) { const f = list.data.grievances.find((g) => g.id === sel.id); if (f) setSel(f); } }, [list.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const create = form.handleSubmit(async (v) => {
    setErr("");
    try {
      const g = await api.createGrievance({ user: userId, issue: v.issue, name: v.name, company: v.company, amount: v.amount, incident_date: v.incident_date,
        details: v.details + (v.desired ? `\nWhat I want: ${v.desired}` : ""), evidence: evLines.split("\n").map((s) => s.trim()).filter(Boolean), lang });
      setSel(g); list.reload(); refresh();
    } catch { setErr(t("err.save", "Could not save. Please check the figures and try again.")); }
  });
  const patch = async (b: Record<string, unknown>) => { if (!sel) return; const g = await api.patchGrievance(sel.id, { user: userId, ...b }); setSel(g); list.reload(); refresh(); };

  return (
    <div className="space-y-4">
      {list.data && list.data.grievances.length > 0 && (
        <Card><CardHeader><CardTitle>{t("g.mine", "My complaints")}</CardTitle></CardHeader><CardContent className="space-y-1 text-sm">
          {list.data.grievances.map((g) => (<button key={g.id} onClick={() => setSel(g)} className="flex w-full items-center justify-between rounded-lg bg-secondary p-2 text-left hover:bg-accent"><span><b>{g.company}</b> · {t(`gi.${g.kind}`, g.kind)}</span><Badge>{t(`gs.${g.status}`, g.status)}</Badge></button>))}
        </CardContent></Card>
      )}

      <form onSubmit={create} noValidate>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><PenLine className="size-4" />{t("g.title", "NyaySaathi - build a complaint")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("g.hint", "Tell us the facts. We write a polite, factual draft in your language. You review and edit it. Nothing is sent anywhere.")}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field id="issue" label={t("g.issue", "What is the problem?")}><Select id="issue" {...form.register("issue")}>{["unpaid_wages", "incentive", "deduction", "deactivation", "contractor"].map((i) => <option key={i} value={i}>{t(`gi.${i}`, i)}</option>)}</Select></Field>
              <Field id="company" label={t("g.company", "Company / platform / contractor")} error={e.company?.message}><Input id="company" {...form.register("company")} /></Field>
              <Field id="name" label={t("g.name", "Your name")} error={e.name?.message}><Input id="name" {...form.register("name")} /></Field>
              <Field id="idate" label={t("g.date", "Date it happened")} error={e.incident_date?.message}><Input id="idate" type="date" {...form.register("incident_date")} /></Field>
              <Field id="gamt" label={t("g.amount", "Amount involved (₹)")} error={e.amount?.message}><Input id="gamt" type="number" step="any" {...form.register("amount", { setValueAs: toNum })} /></Field>
              <Field id="desired" label={t("g.desired", "What outcome do you want?")}><Input id="desired" {...form.register("desired")} /></Field>
            </div>
            <Field id="details" label={t("g.details", "What happened? (facts, dates)")} error={e.details?.message}>
              <Textarea id="details" rows={4} {...form.register("details")} />
            </Field>
            <VoiceButton onText={(txt) => form.setValue("details", (form.getValues("details") + " " + txt).trim(), { shouldValidate: true })} />
            <Field id="evid" label={t("g.evidence", "Evidence you have (one per line - e.g. payout screenshot 17 Oct, wage diary)")}><Textarea id="evid" rows={3} value={evLines} onChange={(ev) => setEvLines(ev.target.value)} /></Field>
            {err && <Alert variant="error">{err}</Alert>}
            <Button type="submit">{t("g.create", "Write the draft")}</Button>
          </CardContent>
        </Card>
      </form>

      {sel && (
        <Card aria-live="polite">
          <CardHeader><CardTitle className="flex flex-wrap items-center gap-2">{t("g.review", "Review and edit your complaint")} <Badge>{t(`gs.${sel.status}`, sel.status)}</Badge></CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <Alert variant="warning">{t("g.note", "Status is recorded by you. GigSaathi drafts letters; it does not submit them or guarantee any outcome.")}</Alert>
            {sel.letter_local && <div><p className="font-semibold">{t("g.local", "Letter in your language")}</p><pre className="whitespace-pre-wrap rounded-lg bg-secondary p-3 font-sans">{sel.letter_local}</pre></div>}
            <Field id="letter" label={t("g.letter", "Letter (English, for sending)")}><Textarea id="letter" rows={12} value={letter} onChange={(ev) => setLetter(ev.target.value)} /></Field>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => patch({ letter })}>{t("g.savedit", "Save my edits")}</Button>
              <Button variant="outline" onClick={() => navigator.clipboard?.writeText(letter)}>{t("g.copy", "Copy letter")}</Button>
              <Button variant="outline" onClick={() => window.print()}><Download />{t("xray.print", "Print / save as PDF")}</Button>
            </div>
            <div>
              <p className="font-semibold">{t("g.status", "Where is this complaint? (you update this)")}</p>
              <div className="mt-1 flex flex-wrap gap-2">{STATUSES.map((s) => <Button key={s} size="sm" variant={sel.status === s ? "default" : "outline"} onClick={() => patch({ status: s })}>{t(`gs.${s}`, s)}</Button>)}</div>
              {sel.follow_ups.length > 0 && <p className="mt-2 text-muted-foreground">{t("g.followups", "Suggested follow-up dates")}: {sel.follow_ups.join(" · ")}</p>}
            </div>
            <div>
              <p className="font-semibold">{t("g.ladder", "Where to escalate, in order")}</p>
              <ol className="ml-4 list-decimal space-y-1">{sel.escalation.map((s) => <li key={s.id}><b>{s.to}</b> - {s.note} <span className="text-muted-foreground">({s.where})</span></li>)}</ol>
              <p className="mt-1 text-xs text-muted-foreground">{t("g.cite", "Channels are described from the platform grievance rules, the labour department process and NALSA (15100). Check the current rules for your state.")}</p>
            </div>
            <div>
              <p className="font-semibold">{t("g.timeline", "Timeline")}</p>
              <ul className="ml-4 list-disc">{sel.timeline.map((x, i) => <li key={i}>{x.day} - {x.event.replace("status:", t("g.statusto", "status: ")).replace("draft_created", t("g.created", "draft created"))}</li>)}</ul>
              <form className="mt-2 flex gap-2" onSubmit={(ev) => { ev.preventDefault(); if (note.trim()) { patch({ event: note }); setNote(""); } }}>
                <label className="sr-only" htmlFor="tlnote">{t("g.addnote", "Add a note")}</label><Input id="tlnote" value={note} onChange={(ev) => setNote(ev.target.value)} placeholder={t("g.addnote.ph", "Add a note (e.g. ticket number, reply received)")} /><Button type="submit" variant="outline">{t("log.save2", "Save")}</Button>
              </form>
            </div>
            {sel.evidence.length > 0 && <div><p className="font-semibold">{t("g.ev", "Evidence listed")}</p><ul className="ml-4 list-disc">{sel.evidence.map((x) => <li key={x}>{x}</li>)}</ul></div>}
          </CardContent>
        </Card>
      )}
      <PracticeMode />
    </div>
  );
}

function PracticeMode() {
  const { t, lang } = useApp();
  const sc = useAsync(() => api.practiceList(lang), [lang]);
  const [id, setId] = useState("");
  const [step, setStep] = useState<{ step: number; npc: string | null; done: boolean } | null>(null);
  const [ans, setAns] = useState("");
  const [log, setLog] = useState<{ who: "npc" | "me" | "coach"; text: string }[]>([]);
  const start = async () => { const s = await api.practiceStart(id || sc.data?.scenarios[0]?.id || "", lang); setStep(s); setLog([{ who: "npc", text: s.npc }]); };
  const send = async () => {
    if (!step || !ans.trim()) return;
    const r = await api.practiceStep(id || sc.data?.scenarios[0]?.id || "", step.step, ans, lang);
    setLog((l) => [...l, { who: "me", text: ans }, { who: "coach", text: `${r.feedback.tip} (${r.feedback.score}/${r.feedback.max})` }, ...(r.npc ? [{ who: "npc" as const, text: r.npc }] : [])]);
    setStep({ step: r.step, npc: r.npc, done: r.done }); setAns("");
  };
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquareWarning className="size-4" />{t("pr.title", "Practice a hard conversation")}</CardTitle></CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">{t("pr.hint", "Rehearse with a contractor, police officer or customer before the real talk. This is a scripted practice with tips, not legal advice.")}</p>
        <div className="flex flex-wrap items-end gap-2"><Field id="sc" label={t("pr.pick", "Situation")}><Select id="sc" value={id} onChange={(ev) => setId(ev.target.value)}>{sc.data?.scenarios.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</Select></Field><Button onClick={start}>{t("b.start", "Start")}</Button></div>
        <div className="space-y-1" aria-live="polite">{log.map((m, i) => <p key={i} className={m.who === "npc" ? "rounded-lg bg-secondary p-2" : m.who === "me" ? "ml-6 rounded-lg bg-primary p-2 text-primary-foreground" : "rounded-lg bg-warning p-2 text-warning-foreground"}>{m.who === "coach" ? "💡 " : ""}{m.text}</p>)}</div>
        {step && !step.done && <form onSubmit={(ev) => { ev.preventDefault(); send(); }} className="flex gap-2"><label className="sr-only" htmlFor="pans">{t("l.reply", "Your reply")}</label><Input id="pans" value={ans} onChange={(ev) => setAns(ev.target.value)} placeholder={t("l.reply", "Your reply")} /><VoiceButton onText={(v) => setAns(v)} /><Button type="submit">{t("b.send", "Send reply")}</Button></form>}
        {step?.done && <Alert variant="info">{t("pr.done", "Practice finished. You can start again anytime.")}</Alert>}
      </CardContent>
    </Card>
  );
}
