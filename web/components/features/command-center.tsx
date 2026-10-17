"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Calculator, FileText, FlaskConical, Landmark, PenLine, ScanLine, ShieldAlert, Timer } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import { rupees } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Skeleton } from "@/components/ui/misc";
import { DataBadge } from "@/components/data-badge";
import { ReadAloud, VoiceButton } from "@/components/voice";
import { OpportunityCards } from "./opportunities";

export function CommandCenter() {
  const { userId, lang, t, setMode, refreshKey, mode } = useApp();
  const router = useRouter();
  const { data, loading, error, reload } = useAsync(() => api.dashboard(userId, lang), [userId, lang, refreshKey]);

  const actions = [
    { href: "/earnings?tab=trip", icon: Calculator, label: t("qa.trip", "Trip Profit") },
    { href: "/earnings?tab=xray", icon: ScanLine, label: t("qa.xray", "Earnings X-Ray") },
    { href: "/rights?tab=schemes", icon: Landmark, label: t("qa.schemes", "Welfare Schemes") },
    { href: "/rights?tab=docs", icon: FileText, label: t("qa.docs", "Document Help") },
    { href: "/rights?tab=grievance", icon: PenLine, label: t("qa.grievance", "Grievance Builder") },
    { href: "/rights?tab=safety", icon: ShieldAlert, label: t("qa.safety", "Safety Center") },
  ];

  return (
    <div className="space-y-5">
      <section className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("home.title", "Your Worker Command Center")}</h1>
          <p className="text-sm text-muted-foreground">{t("home.tagline", "Earn more. Claim what you may be entitled to. Protect your income. Know your rights.")}</p>
        </div>
        <div className="md:w-72"><VoiceButton size="lg" onText={(txt) => router.push(`/saathi?q=${encodeURIComponent(txt)}`)} /></div>
      </section>

      {loading && <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-24" />)}</div>}
      {error && <Alert variant="error" title={t("err.load", "Could not load. Please check your connection and try again.")}><Button size="sm" variant="outline" onClick={reload}>{t("common.retry", "Try again")}</Button></Alert>}

      {data && data.data_source === "empty" && (
        <Card><CardContent className="flex flex-col items-start gap-3 pt-4">
          <h2 className="text-lg font-semibold">{t("home.empty.title", "No shifts saved yet")}</h2>
          <p className="text-sm text-muted-foreground">{t("home.empty.body", "Add today's earnings to see your real net income per hour. Or look around first with clearly-labelled demo data.")}</p>
          <div className="flex flex-wrap gap-2"><Button asChild><Link href="/earnings?tab=log">{t("home.empty.add", "Add a shift")}</Link></Button>
            <Button variant="outline" onClick={() => setMode("demo")}><FlaskConical />{t("home.empty.demo", "Explore with demo data")}</Button></div>
        </CardContent></Card>
      )}

      {data && (
        <>
          <div className="flex items-center gap-2"><h2 className="font-semibold">{t("home.today", "Today")}</h2><DataBadge source={data.data_source} /></div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {[[t("kpi.gross", "Gross income"), rupees(data.today.gross)], [t("kpi.exp", "Expenses"), rupees(data.today.expenses)], [t("kpi.net", "Net income"), rupees(data.today.net)],
              [t("kpi.hours", "Hours worked"), data.today.hours ? String(data.today.hours) : "—"], [t("kpi.ph", "Net per hour"), data.today.net_per_hour ? rupees(data.today.net_per_hour) : "—"]].map(([k, v]) => (
              <Card key={k}><CardContent className="p-3 pt-3"><p className="text-xs text-muted-foreground">{k}</p><p className="text-xl font-bold md:text-2xl">{v}</p></CardContent></Card>))}
          </div>

          <Card>
            <CardHeader><CardTitle className="flex items-center justify-between">{t("home.summary", "Today's summary")}<ReadAloud text={data.ai_summary} /></CardTitle></CardHeader>
            <CardContent><p>{data.ai_summary}</p><p className="mt-1 text-xs text-muted-foreground">{data.summary_basis === "no data" ? t("home.basis.none", "No saved data for today.") : t("home.basis.calc", "Calculated from the shifts you saved. No guesses.")}</p></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("home.week", "This week")} {mode === "demo" && <DataBadge source="demo" />}</CardTitle></CardHeader>
            <CardContent>
              <div className="mb-2 grid grid-cols-3 text-sm"><span>{t("kpi.gross", "Gross income")}: <b>{rupees(data.week.gross)}</b></span><span>{t("kpi.exp", "Expenses")}: <b>{rupees(data.week.expenses)}</b></span><span>{t("kpi.net", "Net income")}: <b>{rupees(data.week.net)}</b></span></div>
              <div className="h-56 w-full" role="img" aria-label={t("home.chart.alt", "Bar chart of gross income, expenses and net income for the last 7 days")}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.series.map((s) => ({ ...s, day: s.day.slice(5) }))}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" fontSize={12} /><YAxis fontSize={12} width={40} />
                    <Tooltip formatter={(v) => rupees(Number(v))} /><Legend />
                    <Bar dataKey="gross" name={t("kpi.gross", "Gross income")} fill="#166534" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expenses" name={t("kpi.exp", "Expenses")} fill="#b45309" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="net" name={t("kpi.net", "Net income")} fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <section aria-label={t("home.quick", "Quick actions")}>
        <h2 className="mb-2 font-semibold">{t("home.quick", "Quick actions")}</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {actions.map((a) => (
            <Link key={a.href} href={a.href} className="flex items-center gap-3 rounded-xl border bg-card p-4 font-semibold shadow-sm hover:bg-accent"><a.icon className="size-7 text-primary" />{a.label}</Link>))}
        </div>
      </section>

      <section><h2 className="mb-2 font-semibold">{t("home.opps", "Today's plan: 3 things worth doing")}</h2><OpportunityCards /></section>

      {data && data.pending.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Timer className="size-4" />{t("home.pending", "Pending: applications, documents, follow-ups")}</CardTitle></CardHeader>
          <CardContent><ul className="space-y-1 text-sm">{data.pending.map((p, i) => (
            <li key={i} className="flex flex-wrap justify-between gap-2 rounded-lg bg-secondary p-2">
              <span><b>{p.type === "scheme" ? t("notif.scheme", "Scheme") : p.type === "grievance" ? t("notif.grievance", "Complaint") : t("notif.doc", "Document expiry")}</b> {String(p.company || p.id)}</span>
              <span className="text-muted-foreground">{p.status}{p.due ? ` · ${p.due}` : ""}{p.days_left !== undefined ? ` · ${p.days_left}d` : ""}{p.follow_up_on ? ` · ${t("pending.followup", "follow up")} ${p.follow_up_on}` : ""}</span>
            </li>))}</ul></CardContent>
        </Card>
      )}
    </div>
  );
}
