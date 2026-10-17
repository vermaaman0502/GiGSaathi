"use client";
import { useState } from "react";
import { FileText, Upload } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { ocrImage } from "@/lib/ocr";
import type { DocAnalysis, SchemeCard } from "@/lib/types";
import { useAsync } from "@/lib/use-async";
import { rupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Select, Textarea } from "@/components/ui/form-controls";
import { Alert, Progress } from "@/components/ui/misc";
import { ReadAloud } from "@/components/voice";

const FORMS = ["eshram", "pmsym", "apy", "pmsby", "pmjjby", "bocw"];

export function Docs() {
  const { t, lang, userId, refresh } = useApp();
  const [text, setText] = useState("");
  const [pct, setPct] = useState<number | null>(null);
  const [res, setRes] = useState<DocAnalysis | null>(null);
  const [err, setErr] = useState("");
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState("eshram");
  const ev = useAsync(() => api.evidence(userId), [userId, saved]);
  const helper = useAsync<SchemeCard>(() => api.scheme(form, lang), [form, lang]);

  const onFile = async (f?: File) => {
    if (!f) return;
    setErr(""); setPct(0);
    try { const out = await ocrImage(f, lang, setPct); if (!out.trim()) throw new Error("empty"); setText(out); }
    catch { setErr(t("doc.ocr.fail", "Could not read this image. Please type or paste the text instead.")); }
    finally { setPct(null); }
  };
  const analyze = async () => { setErr(""); try { setRes(await api.analyzeDoc(text, lang)); setSaved(false); } catch { setErr(t("err.analyze", "Could not analyse. Please try again.")); } };
  const keep = async () => { if (!res) return; await api.addEvidence({ user: userId, kind: res.doc_type, title: `${t(`dt.${res.doc_type}`, res.doc_type)} ${new Date().toISOString().slice(0, 10)}`, data: res }); setSaved(true); refresh(); };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="size-4" />{t("doc.title", "Kagaz Samjho - understand a document")}</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Alert variant="warning">{t("doc.privacy", "The photo is read on your phone and is not uploaded. Only the text you confirm below is sent for analysis. Do not include OTPs, PINs or full Aadhaar numbers.")}</Alert>
          <label className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90"><Upload className="size-4" />{t("doc.upload", "Photo of notice, contract, challan or loan paper")}
            <input type="file" accept="image/*" className="sr-only" onChange={(e) => onFile(e.target.files?.[0])} /></label>
          {pct !== null && <div><Progress value={pct} label={t("xray.progress", "Reading image")} /><p className="mt-1 text-xs text-muted-foreground">{pct}%</p></div>}
          <Field id="doctext" label={t("doc.text", "Document text (check and fix it if needed)")}><Textarea id="doctext" rows={7} value={text} onChange={(e) => setText(e.target.value)} /></Field>
          {err && <Alert variant="error">{err}</Alert>}
          <Button onClick={analyze} disabled={text.trim().length < 15}>{t("doc.analyze", "Explain this document")}</Button>
        </CardContent>
      </Card>

      {res && (
        <Card aria-live="polite">
          <CardHeader><CardTitle className="flex flex-wrap items-center gap-2">{t("doc.result", "What this document says")} <Badge>{t(`dt.${res.doc_type}`, res.doc_type)}</Badge></CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {res.ai_summary ? <div><p>{res.ai_summary}</p><ReadAloud text={res.ai_summary} /></div> : <p className="text-muted-foreground">{t("doc.nosummary", "A plain-language summary needs the AI model, which is not connected. The details below were found by reading the text directly.")}</p>}
            {res.amounts.length > 0 && <p><b>{t("doc.amounts", "Amounts found")}:</b> {res.amounts.map((a) => rupees(a)).join(", ")}</p>}
            {res.dates.length > 0 && <p><b>{t("doc.dates", "Dates found")}:</b> {res.dates.join(", ")}</p>}
            {res.deadlines.length > 0 && <div><b>{t("doc.deadlines", "Deadlines")}</b><ul className="ml-4 list-disc">{res.deadlines.map((d) => <li key={d}>{d}</li>)}</ul></div>}
            {res.fees.length > 0 && <div><b>{t("doc.fees", "Fees and charges")}</b><ul className="ml-4 list-disc">{res.fees.map((d) => <li key={d}>{d}</li>)}</ul></div>}
            {res.obligations.length > 0 && <div><b>{t("doc.oblig", "What you must do")}</b><ul className="ml-4 list-disc">{res.obligations.map((d) => <li key={d}>{d}</li>)}</ul></div>}
            <div>
              <b>{t("doc.risks", "Points to look at more closely")}</b>
              {res.risks.length === 0 ? <p className="text-muted-foreground">{t("doc.norisk", "No obvious risky wording was found - but this check is simple. Read everything and ask someone you trust.")}</p> :
                <ul className="mt-1 space-y-2">{res.risks.map((r) => <li key={r.key} className="rounded-lg bg-warning p-2 text-warning-foreground"><b>{t(`risk.${r.key}`, r.key)}</b><br /><span className="text-xs">&ldquo;{r.snippet}&rdquo;</span></li>)}</ul>}
            </div>
            <div><b>{t("doc.checklist", "Keep these ready")}</b><ul className="ml-4 list-disc">{res.checklist.map((c) => <li key={c}>{c}</li>)}</ul></div>
            <Alert variant="info">{res.disclaimer}</Alert>
            <p className="text-xs text-muted-foreground">{res.note}</p>
            <Button variant="outline" onClick={keep} disabled={saved}>{saved ? t("doc.saved", "Saved to your evidence") : t("doc.save", "Save to my evidence")}</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>{t("form.title", "Guided form help")}</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Field id="fm" label={t("form.pick", "Which form or registration?")}><Select id="fm" value={form} onChange={(e) => setForm(e.target.value)}>{FORMS.map((f) => <option key={f} value={f}>{t(`scheme.${f}`, f)}</option>)}</Select></Field>
          {helper.data && (
            <div className="space-y-2">
              <p className="font-semibold">{helper.data.title}</p>
              <div><b>{t("form.bring", "Bring or keep ready")}</b><ul className="ml-4 list-disc">{helper.data.documents.map((d) => <li key={d}>{d}</li>)}</ul></div>
              <div><b>{t("haq.steps", "Application steps")}</b><ol className="ml-4 list-decimal">{helper.data.steps.map((s) => <li key={s}>{s}</li>)}</ol></div>
              <Button asChild size="sm"><a href={helper.data.apply_url} target="_blank" rel="noopener noreferrer">{t("haq.apply", "Official application link")}</a></Button>
              <p className="text-xs text-muted-foreground">{t("form.note", "We help you prepare. We do not fill or submit the official form for you, and we never ask for your OTP.")}</p>
            </div>)}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>{t("ev.title", "My evidence")}</CardTitle></CardHeader>
        <CardContent className="text-sm">
          {ev.data && ev.data.evidence.length === 0 && <Alert variant="info">{t("ev.empty", "Nothing saved yet. Payout checks and analysed documents appear here.")}</Alert>}
          <ul className="space-y-1">{ev.data?.evidence.map((e) => <li key={e.id} className="flex justify-between rounded-lg bg-secondary p-2"><span>{e.title}</span><span className="text-muted-foreground">{e.day} · {e.kind}</span></li>)}</ul>
        </CardContent>
      </Card>
    </div>
  );
}
