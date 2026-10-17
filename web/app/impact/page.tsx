"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { impactSchema, toNum, type ImpactForm } from "@/lib/schemas";
import { useAsync } from "@/lib/use-async";
import { rupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/form-controls";
import { Alert, Skeleton } from "@/components/ui/misc";
import { DataBadge } from "@/components/data-badge";

const MONEY = ["extra_payment", "benefit_received", "expense_avoided"];
const COUNT = ["scheme_discovered", "application_started", "complaint_submitted", "complaint_resolved", "document_completed"];

export default function ImpactPage() {
  const { t, userId, refreshKey, refresh } = useApp();
  const { data, loading, error } = useAsync(() => api.impact(userId), [userId, refreshKey]);
  const form = useForm<ImpactForm>({ resolver: zodResolver(impactSchema), defaultValues: { kind: "extra_payment", amount: 0, basis: "user_reported", note: "" } });
  const kind = form.watch("kind");
  const isMoney = MONEY.includes(kind);
  const submit = form.handleSubmit(async (v) => { await api.addImpact({ user: userId, ...v, amount: isMoney ? v.amount : 0 }); form.reset({ ...v, amount: 0, note: "" }); refresh(); });
  const cols: [string, "estimated" | "user_reported" | "verified", number | undefined, string][] = [
    [t("imp.est", "Estimated"), "estimated", data?.money.estimated, t("imp.est.note", "Our calculations. NOT money received.")],
    [t("imp.rep", "Reported by you"), "user_reported", data?.money.user_reported, t("imp.rep.note", "What you told us you received or avoided.")],
    [t("imp.ver", "Independently verified"), "verified", data?.money.verified, t("imp.ver.note", "Needs independent confirmation. No integration provides this yet, so it stays at ₹0.")]];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2"><h1 className="text-2xl font-bold">{t("imp.title", "Worker Impact Ledger")}</h1>{data && <DataBadge source={data.data_source} />}</div>
      <p className="text-sm text-muted-foreground">{t("imp.intro", "A discovered scheme or an estimated saving is never counted as money received. Each number below says where it comes from.")}</p>
      {loading && <Skeleton className="h-32" />}
      {error && <Alert variant="error">{t("err.load", "Could not load. Please check your connection and try again.")}</Alert>}
      {data && (
        <>
          <div className="grid gap-3 md:grid-cols-3">{cols.map(([title, basis, val, note]) => (
            <Card key={basis}><CardHeader><CardTitle className="flex items-center justify-between">{title}<DataBadge source={basis} /></CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{rupees(val ?? 0)}</p><p className="text-xs text-muted-foreground">{note}</p></CardContent></Card>))}</div>
          <Card><CardHeader><CardTitle>{t("imp.counts", "Progress (counts, not money)")}</CardTitle></CardHeader><CardContent className="grid grid-cols-2 gap-2 md:grid-cols-5">{COUNT.map((k) => <div key={k} className="rounded-lg bg-secondary p-3 text-center"><p className="text-2xl font-bold">{data.counts[k] ?? 0}</p><p className="text-xs">{t(`ik.${k}`, k)}</p></div>)}</CardContent></Card>
          <Card><CardHeader><CardTitle>{t("imp.byk", "Money you reported")}</CardTitle></CardHeader><CardContent className="space-y-1 text-sm">{MONEY.map((k) => <p key={k} className="flex justify-between"><span>{t(`ik.${k}`, k)}</span><b>{rupees(data.money_by_kind_user_reported[k] ?? 0)}</b></p>)}</CardContent></Card>

          <form onSubmit={submit} noValidate>
            <Card><CardHeader><CardTitle>{t("imp.add", "Record an outcome")}</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-4">
                  <Field id="ik" label={t("imp.kind", "What happened")}><Select id="ik" {...form.register("kind")}>{[...MONEY, ...COUNT].map((k) => <option key={k} value={k}>{t(`ik.${k}`, k)}</option>)}</Select></Field>
                  {isMoney && <Field id="ia" label={t("f.amount", "Amount (₹)")} error={form.formState.errors.amount?.message}><Input id="ia" type="number" step="any" {...form.register("amount", { setValueAs: toNum })} /></Field>}
                  <Field id="ib" label={t("imp.basis", "How sure are you")}><Select id="ib" {...form.register("basis")}><option value="user_reported">{t("imp.b.rep", "I confirm this happened")}</option><option value="estimated">{t("imp.b.est", "This is only an estimate")}</option></Select></Field>
                  <Field id="in" label={t("imp.note", "Note")}><Input id="in" {...form.register("note")} /></Field>
                </div>
                <Button type="submit">{t("log.save2", "Save")}</Button>
              </CardContent></Card>
          </form>

          <Card><CardHeader><CardTitle>{t("imp.history", "History")}</CardTitle></CardHeader><CardContent>
            {data.entries.length === 0 ? <Alert variant="info">{t("imp.empty", "Nothing recorded yet.")}</Alert> :
              <ul className="space-y-1 text-sm">{data.entries.map((e) => <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-secondary p-2"><span>{e.day} · {t(`ik.${e.kind}`, e.kind)} {e.note && `· ${e.note}`}</span><span className="flex items-center gap-2">{MONEY.includes(e.kind) && <b>{rupees(e.amount)}</b>}<Badge variant="outline">{e.basis}</Badge></span></li>)}</ul>}
          </CardContent></Card>
          <ul className="list-disc pl-5 text-xs text-muted-foreground">{data.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </>
      )}
    </div>
  );
}
