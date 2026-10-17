"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { diarySchema, expenseSchema, toNum, tripSchema, type DiaryForm, type ExpenseForm, type TripForm } from "@/lib/schemas";
import type { TripResult } from "@/lib/types";
import { useAsync } from "@/lib/use-async";
import { rupees, today } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/form-controls";
import { Alert, Progress, Skeleton } from "@/components/ui/misc";
import { DataBadge } from "@/components/data-badge";
import { ReadAloud } from "@/components/voice";
import { WeatherCard } from "./weather-card";

function NumField<T extends Record<string, unknown>>({ form, name, label }: { form: ReturnType<typeof useForm<T>>; name: string; label: string }) {
  const err = (form.formState.errors as Record<string, { message?: string }>)[name]?.message;
  return (
    <Field id={name} label={label} error={err}>
      <Input id={name} type="number" inputMode="decimal" step="any" min={0} aria-invalid={!!err} {...form.register(name as never, { setValueAs: toNum })} />
    </Field>
  );
}

/* ---------------- Trip Profit ---------------- */
export function TripTab() {
  const { t, userId, lang } = useApp();
  const form = useForm<TripForm>({ resolver: zodResolver(tripSchema), defaultValues: { fare: 120, distance_km: 8, time_min: 25, return_km: 4, commission_pct: 20, tolls: 0, other_expenses: 0, mileage_kmpl: 40, fuel_price: 100, wear_per_km: 2 } });
  const [res, setRes] = useState<TripResult | null>(null);
  const [err, setErr] = useState("");
  const [vals, setVals] = useState<TripForm | null>(null);
  const submit = form.handleSubmit(async (v) => {
    setErr("");
    try { setRes(await api.trip({ user: userId, lang, ...v })); setVals(v); } catch { setErr(t("err.calc", "Could not calculate. Please try again.")); }
  });
  const verdict = res && (res.verdict === "accept" ? t("trip.accept", "Worth taking") : res.verdict === "marginal" ? t("trip.marginal", "Low profit — think twice") : t("trip.skip", "Not worth it"));
  return (
    <div className="space-y-4">
      <form onSubmit={submit} noValidate>
        <Card>
          <CardHeader><CardTitle>{t("trip.title", "Trip Profit Calculator")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
              <NumField form={form as never} name="fare" label={t("f.fare", "Fare (₹)")} />
              <NumField form={form as never} name="distance_km" label={t("f.km", "Distance (km)")} />
              <NumField form={form as never} name="time_min" label={t("f.min", "Expected time (min)")} />
              <NumField form={form as never} name="return_km" label={t("f.return", "Empty return (km)")} />
              <NumField form={form as never} name="commission_pct" label={t("f.commpct", "Platform commission (%)")} />
              <NumField form={form as never} name="tolls" label={t("f.tolls", "Tolls (₹)")} />
              <NumField form={form as never} name="other_expenses" label={t("f.otherx", "Other expenses (₹)")} />
            </div>
            <details open={["mileage_kmpl", "fuel_price", "wear_per_km"].some((k) => k in form.formState.errors) || undefined} className="rounded-lg bg-secondary p-3"><summary className="cursor-pointer text-sm font-semibold">{t("trip.assume", "Assumptions you can change")}</summary>
              <div className="mt-2 grid gap-3 sm:grid-cols-3">
                <NumField form={form as never} name="mileage_kmpl" label={t("f.mileage", "Fuel efficiency (km per litre)")} />
                <NumField form={form as never} name="fuel_price" label={t("f.fuelprice", "Fuel price (₹ per litre)")} />
                <NumField form={form as never} name="wear_per_km" label={t("f.wear", "Wear & tear (₹ per km)")} />
              </div></details>
            <Button type="submit">{t("ui.calc", "Calculate")}</Button>
          </CardContent>
        </Card>
      </form>
      {err && <Alert variant="error">{err}</Alert>}
      {res && vals && (
        <Card aria-live="polite">
          <CardHeader><CardTitle className="flex flex-wrap items-center gap-2">{t("trip.result", "Result")} <DataBadge source="estimate" />
            <Badge variant={res.verdict === "accept" ? "default" : res.verdict === "marginal" ? "warning" : "destructive"}>{verdict}</Badge></CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
              {[[t("trip.net", "Net profit"), rupees(res.net_profit, 1)], [t("trip.perhr", "Net per hour"), rupees(res.net_per_hour)], [t("trip.costkm", "Cost per km"), rupees(res.cost_per_km, 2)], [t("trip.breakeven", "Break-even fare"), rupees(res.breakeven_fare)]].map(([k, v]) => (
                <div key={k} className="rounded-lg bg-secondary p-3"><p className="text-xs text-muted-foreground">{k}</p><p className="text-lg font-bold">{v}</p></div>))}
            </div>
            <div>
              <p className="font-semibold">{t("trip.calc", "How this was calculated")}</p>
              <p className="text-muted-foreground">{rupees(vals.fare)} − {t("trip.l.comm", "commission")} {rupees(res.commission, 1)} − {t("trip.l.fuel", "fuel")} {rupees(res.fuel_cost, 1)} − {t("trip.l.wear", "wear")} {rupees(res.wear_cost, 1)} − {t("trip.l.tolls", "tolls & other")} {rupees(vals.tolls + vals.other_expenses)} = <b>{rupees(res.net_profit, 1)}</b></p>
              <ul className="ml-4 mt-1 list-disc text-xs text-muted-foreground">{res.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul>
            </div>
            {res.vs_history ? (
              <Alert variant={res.vs_history.better_than_average ? "info" : "warning"}>
                {t("trip.hist", "Your own saved shifts average {avg} per hour. This trip is {diff} per hour {dir} your average.", { avg: rupees(res.vs_history.your_average_net_per_hour), diff: rupees(Math.abs(res.vs_history.difference_per_hour)), dir: res.vs_history.better_than_average ? t("trip.above", "above") : t("trip.below", "below") })}
              </Alert>
            ) : <p className="text-xs text-muted-foreground">{t("trip.nohist", "Save a few shifts to compare trips with your own average.")}</p>}
            <ReadAloud text={`${verdict}. ${t("trip.net", "Net profit")} ${Math.round(res.net_profit)}`} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ---------------- Shift planner ---------------- */
export function ShiftTab() {
  const { t, userId, refreshKey } = useApp();
  const { data, loading, error } = useAsync(() => api.shiftInsights(userId), [userId, refreshKey]);
  const hh = (n: number) => `${String(n).padStart(2, "0")}:00`;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2">{t("shift.title", "Smart Shift Planner")}</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          {loading && <Skeleton className="h-40" />}
          {error && <Alert variant="error">{t("err.load", "Could not load. Please check your connection and try again.")}</Alert>}
          {data && (
            <>
              <p>{data.note}</p>
              {data.bands.length > 0 && (
                <div className="h-48" role="img" aria-label={t("shift.chart.alt", "Average net per hour by start time")}>
                  <ResponsiveContainer width="100%" height="100%"><BarChart data={data.bands.map((b) => ({ ...b, label: `${hh(b.start)}` }))}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" fontSize={12} /><YAxis fontSize={12} width={40} /><Tooltip formatter={(v) => rupees(Number(v))} />
                    <Bar dataKey="avg" name={t("shift.avg", "Average ₹/hour")} fill="#166534" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>
                </div>
              )}
              <ul className="space-y-1">{data.bands.map((b) => (
                <li key={b.start} className="flex flex-wrap justify-between rounded-lg bg-secondary p-2"><span>{hh(b.start)}–{hh(b.end)} · {b.n} {t("shift.shifts", "shifts")}</span>
                  <span>{b.show_range ? `${rupees(b.min)}–${rupees(b.max)} /h (avg ${rupees(b.avg)})` : `${t("shift.fewdata", "too few shifts for a range")}`}</span></li>))}</ul>
              {data.generic && <div><Badge variant="outline">{t("badge.estimate", "Estimate")}</Badge> <span className="text-muted-foreground">{t("shift.generic", "Generic indicative busy windows (not from your data):")} {data.generic.map((g) => `${hh(g.start)}–${hh(g.end)}`).join(", ")}</span></div>}
              <p className="text-xs text-muted-foreground">{t("shift.nogaurantee", "Past results do not guarantee future earnings.")}</p>
            </>
          )}
        </CardContent>
      </Card>
      <WeatherCard />
    </div>
  );
}

/* ---------------- Incentive coach ---------------- */
export function IncentiveTab() {
  const { t, lang } = useApp();
  const [rule, setRule] = useState("");
  const [parsed, setParsed] = useState<{ target: number; reward: number; deadline: string; confidence: string } | null>(null);
  const [done, setDone] = useState(0);
  const [hours, setHours] = useState(4);
  const [prog, setProg] = useState<{ rem: number; per_hr: number; message: string } | null>(null);
  const [target, setTarget] = useState(0);
  const [reward, setReward] = useState(0);
  const parse = async () => {
    const p = await api.incentiveParse(rule);
    setParsed({ target: p.target_trips ?? 0, reward: p.reward ?? 0, deadline: p.deadline_text ?? "", confidence: p.confidence });
    setTarget(p.target_trips ?? 0); setReward(p.reward ?? 0); setProg(null);
  };
  const track = async () => { if (target > 0) setProg(await api.incentiveProgress({ trips_done: done, target_trips: target, reward, hours_left: hours, lang })); };
  return (
    <Card>
      <CardHeader><CardTitle>{t("inc.title", "Incentive Coach")}</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Field id="rule" label={t("inc.rule", "Paste the incentive rule from your app")}><Textarea id="rule" value={rule} onChange={(e) => setRule(e.target.value)} placeholder="Complete 25 trips by Sunday 11 PM and earn ₹500" /></Field>
        <Button onClick={parse} disabled={!rule.trim()}>{t("inc.read", "Read the rule")}</Button>
        {parsed && (
          <div className="space-y-3 rounded-lg bg-secondary p-3">
            <Alert variant="warning">{t("inc.review", "Read automatically (confidence: {c}). Check these numbers - your platform may have extra conditions.", { c: parsed.confidence })}{parsed.deadline && <> {t("inc.deadline", "Deadline mentioned")}: <b>{parsed.deadline}</b></>}</Alert>
            <div className="grid gap-3 sm:grid-cols-4">
              <Field id="tg" label={t("f.target", "Target trips")}><Input id="tg" type="number" min={0} value={target} onChange={(e) => setTarget(Number(e.target.value))} /></Field>
              <Field id="rw" label={t("f.reward", "Reward (₹)")}><Input id="rw" type="number" min={0} value={reward} onChange={(e) => setReward(Number(e.target.value))} /></Field>
              <Field id="dn" label={t("f.done", "Trips done so far")}><Input id="dn" type="number" min={0} value={done} onChange={(e) => setDone(Number(e.target.value))} /></Field>
              <Field id="hl" label={t("f.hoursleft", "Hours left")}><Input id="hl" type="number" min={0} step="any" value={hours} onChange={(e) => setHours(Number(e.target.value))} /></Field>
            </div>
            <Button onClick={track} disabled={target <= 0}>{t("inc.track", "Show my progress")}</Button>
            {prog && (<div aria-live="polite"><Progress value={target ? (done / target) * 100 : 0} label={t("inc.progress", "Progress to target")} /><p className="mt-2">{prog.message}</p><ReadAloud text={prog.message} /></div>)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ---------------- Multi-platform ---------------- */
export function CompareTab() {
  const { t, userId, refreshKey } = useApp();
  const { data, loading } = useAsync(() => api.compare(userId), [userId, refreshKey]);
  if (loading) return <Skeleton className="h-40" />;
  return (
    <Card>
      <CardHeader><CardTitle>{t("cmp.title", "Compare platforms (after expenses)")}</CardTitle></CardHeader>
      <CardContent className="space-y-3 text-sm">
        {data && data.platforms.length > 0 ? (
          <div className="overflow-x-auto"><table className="w-full min-w-96"><thead><tr className="text-left text-xs text-muted-foreground"><th>{t("cmp.platform", "Platform")}</th><th>{t("cmp.shifts", "Shifts")}</th><th>{t("kpi.net", "Net income")}</th><th>{t("kpi.ph", "Net per hour")}</th></tr></thead>
            <tbody>{data.platforms.map((p) => <tr key={p.platform} className="border-t"><td className="py-2 font-semibold">{p.platform}</td><td>{p.shifts}</td><td>{rupees(p.net)}</td><td>{p.net_per_hour ? rupees(p.net_per_hour) : "—"}</td></tr>)}</tbody></table></div>
        ) : <Alert variant="info">{t("cmp.empty", "Save shifts for at least two platforms to compare them.")}</Alert>}
        {data && data.platforms.length === 1 && <Alert variant="info">{t("cmp.one", "Add shifts from a second platform to see a comparison.")}</Alert>}
        <p className="text-xs text-muted-foreground">{t("cmp.note", "Computed only from shifts you entered. GigSaathi has no live connection to any platform.")}</p>
      </CardContent>
    </Card>
  );
}

/* ---------------- Skills ---------------- */
export function SkillsTab() {
  const { t } = useApp();
  const [wt, setWt] = useState("delivery");
  const { data, loading } = useAsync(() => api.skills(wt), [wt]);
  return (
    <Card>
      <CardHeader><CardTitle>{t("skill.title", "Skill-to-Income Planner")}</CardTitle></CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Field id="wt" label={t("f.worktype", "Type of work")}>
          <Select id="wt" value={wt} onChange={(e) => setWt(e.target.value)}>{[["delivery", t("wk.delivery", "Delivery")], ["driver", t("wk.driver", "Driver")], ["domestic", t("wk.domestic", "Domestic work")], ["daily_wage", t("wk.daily", "Daily wage")]].map(([v, l]) => <option key={v} value={v}>{l}</option>)}</Select>
        </Field>
        {loading && <Skeleton className="h-32" />}
        {data && (<>
          <Alert variant="warning">{t("skill.note", "Income ranges are rough indicative figures, not promises. Costs and demand differ by city.")}</Alert>
          {data.ideas.map((i) => (
            <Card key={i.idea}><CardContent className="space-y-1 pt-4">
              <p className="font-semibold">{i.idea}</p>
              <div className="flex flex-wrap gap-2"><Badge>{t("skill.cost", "Cost")}: {rupees(i.cost)}</Badge><Badge variant="outline">{t("skill.extra", "Possible extra")}: ₹{i.extra_per_month}/{t("skill.mo", "month")}</Badge><Badge variant="outline">{t("skill.payback", "Payback")}: {i.payback_months ? `${i.payback_months} ${t("skill.mo", "month")}` : t("skill.immediate", "immediate")}</Badge></div>
              <p className="text-muted-foreground">{t("skill.prereq", "Needs")}: {i.prerequisites}. {t("skill.time", "Time")}: {i.time_needed}.</p>
              <p>{t("skill.support", "Support")}: {i.support}</p>
            </CardContent></Card>))}
          <div><p className="font-semibold">{t("skill.links", "Verified training and job resources")}</p><ul className="ml-4 list-disc">{data.resources.map((r) => <li key={r.url}><a className="text-primary underline" href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a></li>)}</ul></div>
        </>)}
      </CardContent>
    </Card>
  );
}

/* ---------------- Leaks ---------------- */
export function LeaksTab() {
  const { t, userId, refreshKey, refresh } = useApp();
  const { data, loading, reload } = useAsync(() => api.leaks(userId), [userId, refreshKey]);
  const form = useForm<ExpenseForm>({ resolver: zodResolver(expenseSchema), defaultValues: { category: "chai" } });
  const submit = form.handleSubmit(async (v) => { await api.addExpense({ user: userId, ...v }); form.reset({ category: v.category, amount: undefined }); reload(); refresh(); });
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>{t("leak.add", "Add an expense")}</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={submit} noValidate className="flex flex-wrap items-end gap-3">
            <Field id="ecat" label={t("f.category", "What for")} error={form.formState.errors.category?.message}><Input id="ecat" {...form.register("category")} /></Field>
            <Field id="eamt" label={t("f.amount", "Amount (₹)")} error={form.formState.errors.amount?.message}><Input id="eamt" type="number" inputMode="decimal" {...form.register("amount", { setValueAs: toNum })} /></Field>
            <Button type="submit">{t("log.save2", "Save")}</Button>
          </form>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>{t("leak.title", "Expense Leak Finder")}</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          {loading && <Skeleton className="h-20" />}
          {data && data.leaks.length === 0 && <Alert variant="info">{t("leak.none", "No repeated small expenses found yet. Add expenses to look for leaks.")}</Alert>}
          {data?.leaks.map((l) => (<div key={l.category} className="rounded-lg bg-secondary p-3"><p className="font-semibold">{l.category} · {l.times}× · {rupees(l.total)}</p><p>{l.why}</p><p className="text-muted-foreground">{t("leak.validate", "How to check")}: {l.validate}</p></div>))}
          <p className="text-xs text-muted-foreground">{data?.note}</p>
        </CardContent>
      </Card>
    </div>
  );
}

/* ---------------- Wage diary ---------------- */
export function DiaryTab() {
  const { t, userId, refreshKey, refresh } = useApp();
  const { data, loading, reload } = useAsync(() => api.diary(userId), [userId, refreshKey]);
  const form = useForm<DiaryForm>({ resolver: zodResolver(diarySchema), defaultValues: { day: today(), employer: "", work: "", hours: 8, promised: 0, received: 0 } });
  const submit = form.handleSubmit(async (v) => { await api.addDiary({ user: userId, ...v }); reload(); refresh(); });
  const e = form.formState.errors;
  return (
    <div className="space-y-4">
      <form onSubmit={submit} noValidate>
        <Card>
          <CardHeader><CardTitle>{t("diary.title", "Wage diary")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("diary.hint", "A dated record of work, promised wages and what you actually received. It can help if wages are unpaid.")}</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field id="dd" label={t("f.date", "Date")} error={e.day?.message}><Input id="dd" type="date" {...form.register("day")} /></Field>
              <Field id="de" label={t("f.employer", "Employer / contractor")}><Input id="de" {...form.register("employer")} /></Field>
              <Field id="dw" label={t("f.work", "Work done")}><Input id="dw" {...form.register("work")} /></Field>
              <Field id="dh" label={t("f.hours", "Hours worked")} error={e.hours?.message}><Input id="dh" type="number" step="any" {...form.register("hours", { setValueAs: toNum })} /></Field>
              <Field id="dp" label={t("f.promised2", "Wage promised (₹)")} error={e.promised?.message}><Input id="dp" type="number" step="any" {...form.register("promised", { setValueAs: toNum })} /></Field>
              <Field id="dr" label={t("f.received2", "Wage received (₹)")} error={e.received?.message}><Input id="dr" type="number" step="any" {...form.register("received", { setValueAs: toNum })} /></Field>
            </div>
            <Button type="submit">{t("log.save2", "Save")}</Button>
          </CardContent>
        </Card>
      </form>
      {loading && <Skeleton className="h-24" />}
      {data && (
        <Card><CardContent className="space-y-2 pt-4 text-sm">
          <div className="flex flex-wrap gap-4"><span>{t("diary.promised", "Promised")}: <b>{rupees(data.promised_total)}</b></span><span>{t("diary.received", "Received")}: <b>{rupees(data.received_total)}</b></span><span>{t("diary.unpaid", "Unpaid")}: <b className="text-destructive">{rupees(data.unpaid_total)}</b></span></div>
          {data.entries.length === 0 ? <Alert variant="info">{t("diary.empty", "No entries yet.")}</Alert> :
            <ul className="space-y-1">{data.entries.map((x) => <li key={x.id} className="flex flex-wrap justify-between rounded-lg bg-secondary p-2"><span>{x.day} · {x.employer || "—"} · {x.work}</span><span>{rupees(x.received)} / {rupees(x.promised)}</span></li>)}</ul>}
          <Button asChild variant="outline" size="sm"><a href={api.exportUrl(userId)} download><Download />{t("xray.export", "Download evidence (CSV)")}</a></Button>
        </CardContent></Card>
      )}
    </div>
  );
}
