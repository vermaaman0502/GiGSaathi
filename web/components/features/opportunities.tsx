"use client";
import Link from "next/link";
import { ArrowRight, PiggyBank, ShieldCheck, TrendingUp } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/use-async";
import type { Opportunity } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Skeleton } from "@/components/ui/misc";
import { DataBadge } from "@/components/data-badge";
import { ReadAloud } from "@/components/voice";

const ICON = { earn_more: TrendingUp, save_money: PiggyBank, rights_benefits: ShieldCheck };

export function OpportunityCards() {
  const { userId, lang, t, refreshKey } = useApp();
  const { data, loading, error } = useAsync(() => api.opportunities(userId, lang), [userId, lang, refreshKey]);
  const label = (c: Opportunity["category"]) => c === "earn_more" ? t("opp.earn", "Earn more") : c === "save_money" ? t("opp.save", "Save money") : t("opp.rights", "Benefits & rights");
  const conf = (c: string) => c === "none" ? t("opp.conf.none", "No prediction - not enough data") : t(`opp.conf.${c}`, `Confidence: ${c}`);
  if (loading) return <div className="grid gap-3 md:grid-cols-3"><Skeleton className="h-48" /><Skeleton className="h-48" /><Skeleton className="h-48" /></div>;
  if (error || !data) return <Alert variant="error">{t("err.load", "Could not load. Please check your connection and try again.")}</Alert>;
  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-3">
        {data.items.map((o) => {
          const Icon = ICON[o.category];
          return (
            <Card key={o.category} className="flex flex-col">
              <CardHeader>
                <div className="flex items-center justify-between"><Badge className="gap-1"><Icon className="size-3" />{label(o.category)}</Badge><Badge variant="outline">{t("opp.effort", "Effort")}: {o.effort}</Badge></div>
                <CardTitle className="pt-1">{o.title}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-2 text-sm">
                <p>{o.why}</p>
                {o.evidence.length > 0 && <details><summary className="cursor-pointer font-semibold">{t("opp.evidence", "Data used")}</summary><ul className="ml-4 list-disc text-muted-foreground">{o.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul></details>}
                <div className="flex flex-wrap items-center gap-2">
                  {o.impact ? <><DataBadge source={o.impact.basis as "estimated"} /><span className="text-xs text-muted-foreground">{o.impact.note}</span></> : <Badge variant="outline">{t("opp.impact.none", "Impact not calculable yet")}</Badge>}
                </div>
                <p className="text-xs text-muted-foreground">{conf(o.confidence)}</p>
                <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-2"><Button asChild size="sm" className="h-auto min-h-9 whitespace-normal py-2 text-left"><Link href={o.next.href}>{o.next.label}<ArrowRight /></Link></Button><ReadAloud text={`${o.title}. ${o.why}`} /></div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground">{t("opp.safety", "Never work unsafe hours, take risky loans or overspend because of a suggestion. Rest and safety come first.")}</p>
    </div>
  );
}
