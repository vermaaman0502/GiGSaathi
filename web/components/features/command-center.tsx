"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bars } from "@/components/charts";
import { BarChart3, Calculator, ChevronRight, Clock, FileText, FlaskConical, Gauge, Landmark, PenLine, Receipt, ScanLine, ShieldAlert, Sparkles, Timer, TrendingUp, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";
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
    { href: "/earnings?tab=trip", icon: Calculator, label: t("qa.trip", "Trip Profit"), sub: t("qa.trip.sub", "Is this ride worth it?"), tone: "bg-success-soft text-success" },
    { href: "/earnings?tab=xray", icon: ScanLine, label: t("qa.xray", "Earnings X-Ray"), sub: t("qa.xray.sub", "Check a payout"), tone: "bg-info-soft text-info" },
    { href: "/rights?tab=schemes", icon: Landmark, label: t("qa.schemes", "Welfare Schemes"), sub: t("qa.schemes.sub", "What you may get"), tone: "bg-amber-soft text-amber" },
    { href: "/rights?tab=docs", icon: FileText, label: t("qa.docs", "Document Help"), sub: t("qa.docs.sub", "Understand any paper"), tone: "bg-info-soft text-info" },
    { href: "/rights?tab=grievance", icon: PenLine, label: t("qa.grievance", "Grievance Builder"), sub: t("qa.grievance.sub", "Draft a complaint"), tone: "bg-amber-soft text-amber" },
    { href: "/rights?tab=safety", icon: ShieldAlert, label: t("qa.safety", "Safety Center"), sub: t("qa.safety.sub", "112, alerts, SOS"), tone: "bg-destructive/10 text-destructive" },
  ];
  const kpis = data ? [
    { k: t("kpi.gross", "Gross income"), v: rupees(data.today.gross), icon: Wallet, tone: "bg-success-soft text-success" },
    { k: t("kpi.exp", "Expenses"), v: rupees(data.today.expenses), icon: Receipt, tone: "bg-amber-soft text-amber" },
    { k: t("kpi.net", "Net income"), v: rupees(data.today.net), icon: TrendingUp, tone: "bg-info-soft text-info", main: true },
    { k: t("kpi.hours", "Hours worked"), v: data.today.hours ? String(data.today.hours) : "—", icon: Clock, tone: "bg-muted text-foreground" },
    { k: t("kpi.ph", "Net per hour"), v: data.today.net_per_hour ? rupees(data.today.net_per_hour) : "—", icon: Gauge, tone: "bg-success-soft text-success" },
  ] : [];
  const weekEmpty = !!data && data.series.every((d) => !d.gross && !d.expenses && !d.net);

  return (
    <div className="space-y-6">
      <section className="hero relative overflow-hidden rounded-3xl p-6 text-white shadow-card md:p-8">
        <div aria-hidden className="pointer-events-none absolute -right-10 -top-10 size-48 rounded-full bg-white/10 blur-2xl" />
        <div className="relative flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur"><Sparkles className="size-3.5" />{t("home.kicker", "Your AI work companion")}</p>
            <h1 className="text-2xl font-bold leading-tight md:text-3xl">{t("home.title", "Your Worker Command Center")}</h1>
            <p className="mt-1.5 text-sm text-white/80 md:text-base">{t("home.tagline", "Earn more. Claim what you may be entitled to. Protect your income. Know your rights.")}</p>
          </div>
          <div className="md:w-64 [&_button]:bg-white [&_button]:text-[hsl(142_64%_20%)] [&_button:hover]:bg-white/90"><VoiceButton size="lg" onText={(txt) => router.push(`/saathi?q=${encodeURIComponent(txt)}`)} /></div>
        </div>
      </section>

      {loading && <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}</div>}
      {error && <Alert variant="error" title={t("err.load", "Could not load. Please check your connection and try again.")}><Button size="sm" variant="outline" onClick={reload}>{t("common.retry", "Try again")}</Button></Alert>}

      {data && data.data_source === "empty" && (
        <Card className="border-dashed"><CardContent className="flex flex-col items-start gap-3 pt-5">
          <span className="grid size-11 place-items-center rounded-2xl bg-success-soft text-success"><BarChart3 className="size-5" /></span>
          <h2 className="text-lg font-semibold">{t("home.empty.title", "No shifts saved yet")}</h2>
          <p className="text-sm text-muted-foreground">{t("home.empty.body", "Add today's earnings to see your real net income per hour. Or look around first with clearly-labelled demo data.")}</p>
          <div className="flex flex-wrap gap-2"><Button asChild><Link href="/earnings?tab=log">{t("home.empty.add", "Add a shift")}</Link></Button>
            <Button variant="outline" onClick={() => setMode("demo")}><FlaskConical />{t("home.empty.demo", "Explore with demo data")}</Button></div>
        </CardContent></Card>
      )}

      {data && (
        <>
          <div className="flex items-center gap-2"><h2 className="text-lg font-semibold">{t("home.today", "Today")}</h2><DataBadge source={data.data_source} /></div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {kpis.map(({ k, v, icon: Icon, tone, main }) => (
              <Card key={k} className={cn("transition-shadow hover:shadow-md", main && "col-span-2 ring-1 ring-primary/20 md:col-span-1")}>
                <CardContent className="p-4 pt-4">
                  <span className={cn("mb-3 grid size-9 place-items-center rounded-xl", tone)}><Icon className="size-[18px]" /></span>
                  <p className="text-xs font-medium text-muted-foreground">{k}</p>
                  <p className="num mt-0.5 text-2xl font-bold tracking-tight">{v}</p>
                </CardContent>
              </Card>))}
          </div>

          <Card>
            <CardHeader><CardTitle className="flex items-center justify-between gap-2"><span className="flex items-center gap-2"><span className="grid size-8 place-items-center rounded-lg bg-primary/10 text-primary"><Sparkles className="size-4" /></span>{t("home.summary", "Today's summary")}</span><ReadAloud text={data.ai_summary} /></CardTitle></CardHeader>
            <CardContent><p className="leading-relaxed">{data.ai_summary}</p><p className="mt-1 text-xs text-muted-foreground">{data.summary_basis === "no data" ? t("home.basis.none", "No saved data for today.") : t("home.basis.calc", "Calculated from the shifts you saved. No guesses.")}</p></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t("home.week", "This week")} {mode === "demo" && <DataBadge source="demo" />}</CardTitle></CardHeader>
            <CardContent>
              <div className="mb-4 grid grid-cols-3 gap-2">
                {[[t("kpi.gross", "Gross income"), data.week.gross, "text-success"], [t("kpi.exp", "Expenses"), data.week.expenses, "text-amber"], [t("kpi.net", "Net income"), data.week.net, "text-info"]].map(([k, v, c]) => (
                  <div key={k as string} className="rounded-xl bg-muted/60 p-3"><p className="text-xs text-muted-foreground">{k}</p><p className={cn("num text-lg font-bold", c as string)}>{rupees(v as number)}</p></div>))}
              </div>
              {weekEmpty ? (
                <div className="grid h-40 place-items-center rounded-xl border border-dashed text-center text-sm text-muted-foreground"><span><BarChart3 className="mx-auto mb-2 size-6" />{t("home.week.empty", "Your weekly chart appears after you save your first shift.")}</span></div>
              ) : <div className="h-56 w-full" role="img" aria-label={t("home.chart.alt", "Bar chart of gross income, expenses and net income for the last 7 days")}>
                <Bars data={data.series.map((s) => ({ ...s, day: s.day.slice(5) }))} xKey="day" legend series={[
                  { key: "gross", name: t("kpi.gross", "Gross income"), color: "#16a34a" },
                  { key: "expenses", name: t("kpi.exp", "Expenses"), color: "#d97706" },
                  { key: "net", name: t("kpi.net", "Net income"), color: "#2563eb" },
                ]} />
              </div>}
            </CardContent>
          </Card>
        </>
      )}

      <section aria-label={t("home.quick", "Quick actions")}>
        <h2 className="mb-3 text-lg font-semibold">{t("home.quick", "Quick actions")}</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {actions.map((a) => (
            <Link key={a.href} href={a.href} className="group flex items-center gap-3 rounded-2xl border bg-card p-4 shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md">
              <span className={cn("grid size-11 shrink-0 place-items-center rounded-xl", a.tone)}><a.icon className="size-5" /></span>
              <span className="min-w-0 flex-1"><span className="block font-semibold leading-tight">{a.label}</span><span className="hidden text-xs text-muted-foreground sm:block">{a.sub}</span></span>
              <ChevronRight className="hidden size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 sm:block" />
            </Link>))}
        </div>
      </section>

      <section><h2 className="mb-3 text-lg font-semibold">{t("home.opps", "Today's plan: 3 things worth doing")}</h2><OpportunityCards /></section>

      {data && data.pending.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Timer className="size-4" />{t("home.pending", "Pending: applications, documents, follow-ups")}</CardTitle></CardHeader>
          <CardContent><ul className="space-y-1 text-sm">{data.pending.map((p, i) => (
            <li key={i} className="flex flex-wrap justify-between gap-2 rounded-xl bg-muted/70 p-3">
              <span><b>{p.type === "scheme" ? t("notif.scheme", "Scheme") : p.type === "grievance" ? t("notif.grievance", "Complaint") : t("notif.doc", "Document expiry")}</b> {String(p.company || p.id)}</span>
              <span className="text-muted-foreground">{p.status}{p.due ? ` · ${p.due}` : ""}{p.days_left !== undefined ? ` · ${p.days_left}d` : ""}{p.follow_up_on ? ` · ${t("pending.followup", "follow up")} ${p.follow_up_on}` : ""}</span>
            </li>))}</ul></CardContent>
        </Card>
      )}
    </div>
  );
}
