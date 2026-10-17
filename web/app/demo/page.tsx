"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, Circle, FlaskConical } from "lucide-react";
import { useApp } from "@/app/providers";
import { safeGet, safeSet } from "@/lib/user";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/misc";

export default function DemoPage() {
  const { t, mode, setMode } = useApp();
  const [done, setDone] = useState<string[]>([]);
  useEffect(() => { try { setDone(JSON.parse(safeGet("gs_demo_steps") || "[]")); } catch { setDone([]); } }, []);
  const mark = (id: string) => { const n = Array.from(new Set([...done, id])); setDone(n); safeSet("gs_demo_steps", JSON.stringify(n)); };
  const steps = [
    { id: "earn", href: "/earnings?tab=log", title: t("demo.s1", "1. A worker enters earnings"), body: t("demo.s1b", "Open Log shift. The demo worker already has 14 days of synthetic shifts on two imaginary apps; add one yourself.") },
    { id: "xray", href: "/earnings?tab=xray", title: t("demo.s2", "2. AI-assisted payout analysis"), body: t("demo.s2b", "Tap 'Use synthetic demo payout', review the figures it read, then 'Check my payout'. You will see a possible ₹160 shortfall, explained without calling it fraud.") },
    { id: "trip", href: "/earnings?tab=trip", title: t("demo.s3", "3. Trip profitability comparison"), body: t("demo.s3b", "Calculate a trip and compare it with the demo worker's own average per hour.") },
    { id: "haq", href: "/rights?tab=schemes", title: t("demo.s4", "4. Welfare scheme discovery"), body: t("demo.s4b", "Answer the short questions. Each card shows its source, whether it is verified, and why you may or may not qualify.") },
    { id: "grv", href: "/rights?tab=grievance", title: t("demo.s5", "5. Complaint draft from evidence"), body: t("demo.s5b", "Create a draft from the payout evidence. Review it, edit it and set its status yourself. Nothing is submitted.") },
    { id: "imp", href: "/impact", title: t("demo.s6", "6. Impact dashboard"), body: t("demo.s6b", "See estimates, your own reports and verified outcomes kept apart. The verified column stays at ₹0 on purpose.") },
  ];
  return (
    <div className="space-y-4">
      <h1 className="flex items-center gap-2 text-2xl font-bold"><FlaskConical />{t("demo.title", "Hackathon demo walkthrough")}</h1>
      <Alert variant="warning" title={t("demo.honest.t", "Everything here is synthetic")}>{t("demo.honest", "The worker, payouts and documents are invented. No real worker documents are used. No external submission is made or simulated - drafts stay drafts, and nothing is sent to any platform, department or scheme.")}</Alert>
      {mode !== "demo" ? <Button size="lg" onClick={() => setMode("demo")}>{t("demo.start", "Start demo with synthetic data")}</Button> : <Alert variant="info">{t("demo.on", "Demo mode is ON. Your real records are untouched.")} <button className="underline" onClick={() => setMode("real")}>{t("demo.exit", "Switch to my data")}</button></Alert>}
      <ol className="space-y-3">{steps.map((s) => (
        <Card key={s.id}><CardHeader><CardTitle className="flex items-center gap-2">{done.includes(s.id) ? <CheckCircle2 className="size-5 text-primary" /> : <Circle className="size-5" />}{s.title}</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm"><p>{s.body}</p><Button asChild size="sm" variant={done.includes(s.id) ? "outline" : "default"} onClick={() => mark(s.id)}><Link href={s.href}>{t("demo.open", "Open")}</Link></Button></CardContent></Card>))}</ol>
    </div>
  );
}
