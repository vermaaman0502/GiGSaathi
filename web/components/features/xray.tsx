"use client";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Download, FileImage, FlaskConical, Printer, Upload } from "lucide-react";
import { useApp } from "@/app/providers";
import { api, ApiError } from "@/lib/api";
import { ocrImage } from "@/lib/ocr";
import { shiftSchema, toNum, type ShiftForm } from "@/lib/schemas";
import type { Grievance, ProofResult } from "@/lib/types";
import { rupees, today } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Textarea } from "@/components/ui/form-controls";
import { Alert, Progress } from "@/components/ui/misc";
import { Badge } from "@/components/ui/badge";
import { DataBadge } from "@/components/data-badge";
import { ReadAloud } from "@/components/voice";

const DEFAULTS: ShiftForm = { platform: "", day: today(), hours: 0, gross: 0, commission: 0, deductions: 0, incentive: 0, fuel: 0, other_expenses: 0 };

export function XRay({ withUpload }: { withUpload: boolean }) {
  const { t, userId, lang, mode, refresh } = useApp();
  const form = useForm<ShiftForm>({ resolver: zodResolver(shiftSchema), defaultValues: DEFAULTS });
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = form;
  const [pct, setPct] = useState<number | null>(null);
  const [extracted, setExtracted] = useState<{ confidence: string; note: string; demo: boolean } | null>(null);
  const [pasted, setPasted] = useState("");
  const [msg, setMsg] = useState<{ kind: "error" | "info"; text: string } | null>(null);
  const [result, setResult] = useState<ProofResult | null>(null);
  const [complaint, setComplaint] = useState<{ name: string; company: string }>({ name: "", company: "" });
  const [grievance, setGrievance] = useState<Grievance | null>(null);

  const fillFromText = async (text: string, demo = false) => {
    const r = await api.extractPayout(text);
    const f = r.fields as Record<string, unknown>;
    const n = (k: string) => (typeof f[k] === "number" ? (f[k] as number) : undefined);
    const ded = Array.isArray(f.deductions) ? (f.deductions as { amount: number }[]).reduce((a, d) => a + d.amount, 0) : 0;
    reset({ ...DEFAULTS, platform: demo ? "SwiftEats (demo)" : "", gross: n("gross") ?? 0, commission: n("commission") ?? 0, incentive: n("incentive") ?? 0, deductions: ded, hours: n("hours") ?? 0, received: n("received") });
    setExtracted({ confidence: r.confidence, note: r.note, demo });
    setResult(null); setGrievance(null);
  };

  const onFile = async (file: File | undefined) => {
    if (!file) return;
    setMsg(null); setPct(0);
    try {
      const text = await ocrImage(file, lang, (p) => setPct(p));
      if (!text.trim()) throw new Error("empty");
      await fillFromText(text);
    } catch {
      setMsg({ kind: "error", text: t("xray.ocr.fail", "Could not read this image. Paste the text below or type the figures by hand.") });
    } finally { setPct(null); }
  };

  const loadDemo = async () => {
    const d = await api.demoPayout();
    await fillFromText(d.text, true);
    setMsg({ kind: "info", text: t("xray.demo.loaded", "Loaded a SYNTHETIC demo payout. It is not a real worker's record.") });
  };

  const onSubmit = handleSubmit(async (v) => {
    setMsg(null);
    try {
      const r = await api.proof({ user: userId, ...v, lang, source: extracted ? (extracted.demo ? "demo" : "ocr") : "manual", save: true });
      setResult(r); refresh();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError && e.status === 0 ? t("err.offline", "You seem to be offline. Your entries on this screen are kept - try again when connected.") : t("err.save", "Could not save. Please check the figures and try again.") });
    }
  });

  const draftComplaint = async () => {
    if (!result) return;
    if (complaint.name.trim().length < 2 || complaint.company.trim().length < 2) { setMsg({ kind: "error", text: t("xray.complaint.need", "Enter your name and the company name.") }); return; }
    try {
      const rec = result.validated_record as { day?: string };
      const g = await api.createGrievance({ user: userId, issue: "deduction", name: complaint.name, company: complaint.company, amount: result.explanation.shortfall, incident_date: rec.day,
        details: "The payout received is lower than the platform's own figures add up to.", evidence: result.evidence.map((e) => `${e.label}: ${e.detail}`), lang });
      setGrievance(g); refresh(); setMsg(null);
    } catch { setMsg({ kind: "error", text: t("err.save", "Could not save. Please check the figures and try again.") }); }
  };

  const num = (name: keyof ShiftForm, label: string, opts: { optional?: boolean; step?: string } = {}) => (
    <Field id={name} label={label} error={errors[name]?.message as string | undefined}>
      <Input id={name} type="number" inputMode="decimal" step={opts.step || "any"} min={0} aria-invalid={!!errors[name]} {...register(name, { setValueAs: toNum })} />
    </Field>
  );
  const c = result?.calculation;

  return (
    <div className="space-y-4">
      {withUpload && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><FileImage className="size-4" />{t("xray.upload.title", "Upload a payout screenshot")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("xray.upload.hint", "The photo is read on your phone. It is not uploaded. You will review every figure before anything is saved.")}</p>
            <div className="flex flex-wrap gap-2">
              <label className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
                <Upload className="size-4" />{t("xray.upload.btn", "Choose image")}
                <input type="file" accept="image/*" className="sr-only" onChange={(e) => onFile(e.target.files?.[0])} />
              </label>
              <Button type="button" variant="outline" onClick={loadDemo}><FlaskConical />{t("xray.demo.btn", "Use synthetic demo payout")}</Button>
            </div>
            {pct !== null && <div><Progress value={pct} label={t("xray.progress", "Reading image")} /><p className="mt-1 text-xs text-muted-foreground">{t("xray.progress", "Reading image")}… {pct}%</p></div>}
            <details><summary className="cursor-pointer text-sm font-semibold">{t("xray.paste", "Or paste payout text")}</summary>
              <Textarea value={pasted} onChange={(e) => setPasted(e.target.value)} className="mt-2" placeholder={"Total earnings 1100\nPlatform fee 220\nBonus 200\nNet payout 880"} />
              <Button type="button" size="sm" className="mt-2" onClick={() => pasted.trim() && fillFromText(pasted)}>{t("xray.paste.btn", "Read this text")}</Button></details>
          </CardContent>
        </Card>
      )}

      {msg && <Alert variant={msg.kind === "error" ? "error" : "info"}>{msg.text}</Alert>}
      {extracted && (
        <Alert variant="warning" title={t("xray.review.title", "Please review before saving")}>
          {t("xray.review.body", "These figures were read automatically and may be wrong. Confidence: {c}. Correct anything that does not match your screenshot.", { c: extracted.confidence })}
          {extracted.demo && <> <DataBadge source="demo" /></>}
        </Alert>
      )}

      <form onSubmit={onSubmit} noValidate>
        <Card>
          <CardHeader><CardTitle>{withUpload ? t("xray.form.title", "Review and check") : t("log.title", "Log a shift")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              <Field id="platform" label={t("f.platform", "App / platform / employer")} error={errors.platform?.message}><Input id="platform" aria-invalid={!!errors.platform} {...register("platform")} /></Field>
              <Field id="day" label={t("f.date", "Date")} error={errors.day?.message}><Input id="day" type="date" {...register("day")} /></Field>
              {num("hours", t("f.hours", "Hours worked"))}
              {num("start_hour", t("f.start", "Start hour (0-23, optional)"), { step: "1" })}
              {num("gross", t("f.gross", "Gross earnings (₹)"))}
              {num("incentive", t("f.incentive", "Incentives (₹)"))}
              {num("commission", t("f.commission", "Commission / platform fee (₹)"))}
              {num("deductions", t("f.deductions", "Other deductions (₹)"))}
              {num("fuel", t("f.fuel", "Fuel (₹)"))}
              {num("other_expenses", t("f.other", "Other expenses (₹)"))}
              {num("promised", t("f.promised", "Promised amount (₹, optional)"))}
              {num("received", t("f.received", "Amount you received (₹)"))}
            </div>
            <Button type="submit" disabled={isSubmitting}>{withUpload ? t("xray.run", "Check my payout") : t("log.save", "Save shift")}</Button>
          </CardContent>
        </Card>
      </form>

      {result && c && (
        <Card aria-live="polite">
          <CardHeader><CardTitle className="flex flex-wrap items-center gap-2">{t("xray.result", "Result")}<DataBadge source={mode === "demo" ? "demo" : "user"} />
            <Badge variant={result.explanation.code === "possible_discrepancy" ? "warning" : "secondary"}>{result.explanation.code === "possible_discrepancy" ? t("xray.flag", "Possible discrepancy") : result.explanation.code === "no_discrepancy" ? t("xray.ok", "Numbers add up") : t("xray.unknown", "Need amount received")}</Badge></CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <table className="w-full"><tbody>
              <tr><td>{t("xray.t.total", "Figures add up to (gross + incentives − commission − deductions)")}</td><td className="text-right font-semibold">{rupees(c.platform_total)}</td></tr>
              <tr><td>{t("xray.t.received", "You received")}</td><td className="text-right font-semibold">{rupees(c.received)}</td></tr>
              {c.promised !== null && <tr><td>{t("xray.t.promised", "Promised")}</td><td className="text-right font-semibold">{rupees(c.promised)}</td></tr>}
              <tr><td>{t("xray.t.short", "Possible shortfall")}</td><td className="text-right font-semibold">{rupees(result.explanation.shortfall)}</td></tr>
              <tr><td>{t("xray.t.take", "Your take-home after fuel and other costs")}</td><td className="text-right font-semibold">{rupees(c.take_home)}</td></tr>
            </tbody></table>
            <p>{result.explanation.message}</p><ReadAloud text={result.explanation.message} />
            <p className="text-xs text-muted-foreground">{t("xray.disclaimer", "This is a possible discrepancy based on the numbers you entered or confirmed. It is not proof of wrongdoing.")}</p>
            <div><p className="font-semibold">{t("xray.evidence", "Evidence saved")}</p><ul className="ml-4 list-disc text-muted-foreground">{result.evidence.map((e, i) => <li key={i}><b>{e.label}:</b> {e.detail}</li>)}</ul></div>
            {result.explanation.code === "possible_discrepancy" && !grievance && (
              <div className="space-y-2 rounded-lg bg-secondary p-3">
                <p className="font-semibold">{t("xray.next", "Next step")}: {result.next_step?.message}</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <Field id="cn" label={t("xray.name", "Your name")}><Input id="cn" value={complaint.name} onChange={(e) => setComplaint({ ...complaint, name: e.target.value })} /></Field>
                  <Field id="cc" label={t("xray.company", "Company / platform")}><Input id="cc" value={complaint.company} onChange={(e) => setComplaint({ ...complaint, company: e.target.value })} /></Field>
                </div>
                <Button type="button" onClick={draftComplaint}>{t("xray.draft", "Draft a complaint from this evidence")}</Button>
              </div>
            )}
            {grievance && (
              <Alert variant="info" title={t("xray.drafted", "Draft saved (not submitted)")}>
                <Link href="/rights?tab=grievance" className="font-semibold underline">{t("xray.drafted.open", "Review and edit your complaint")}</Link>
              </Alert>
            )}
            <div className="no-print flex flex-wrap gap-2">
              <Button asChild variant="outline" size="sm"><a href={api.exportUrl(userId)} download><Download />{t("xray.export", "Download evidence (CSV)")}</a></Button>
              <Button variant="outline" size="sm" onClick={() => window.print()}><Printer />{t("xray.print", "Print / save as PDF")}</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
