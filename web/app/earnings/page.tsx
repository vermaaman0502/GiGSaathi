"use client";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useApp } from "@/app/providers";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/misc";
import { XRay } from "@/components/features/xray";
import { CompareTab, DiaryTab, IncentiveTab, LeaksTab, ShiftTab, SkillsTab, TripTab } from "@/components/features/earn-tools";

function Inner() {
  const { t } = useApp();
  const router = useRouter();
  const tab = useSearchParams().get("tab") || "xray";
  const tabs: [string, string][] = [["xray", t("et.xray", "Earnings X-Ray")], ["log", t("et.log", "Log shift")], ["trip", t("et.trip", "Trip profit")], ["shift", t("et.shift", "Shift planner")],
    ["incentive", t("et.incentive", "Incentives")], ["compare", t("et.compare", "Compare apps")], ["skills", t("et.skills", "Skills")], ["leaks", t("et.leaks", "Leaks")], ["diary", t("et.diary", "Wage diary")]];
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t("nav.earnings", "Earnings")}</h1>
      <Tabs value={tab} onValueChange={(v) => router.replace(`/earnings?tab=${v}`)}>
        <TabsList aria-label={t("nav.earnings", "Earnings")}>{tabs.map(([v, l]) => <TabsTrigger key={v} value={v}>{l}</TabsTrigger>)}</TabsList>
        <TabsContent value="xray"><XRay withUpload /></TabsContent>
        <TabsContent value="log"><XRay withUpload={false} /></TabsContent>
        <TabsContent value="trip"><TripTab /></TabsContent>
        <TabsContent value="shift"><ShiftTab /></TabsContent>
        <TabsContent value="incentive"><IncentiveTab /></TabsContent>
        <TabsContent value="compare"><CompareTab /></TabsContent>
        <TabsContent value="skills"><SkillsTab /></TabsContent>
        <TabsContent value="leaks"><LeaksTab /></TabsContent>
        <TabsContent value="diary"><DiaryTab /></TabsContent>
      </Tabs>
    </div>
  );
}
export default function Page() { return <Suspense fallback={null}><Inner /></Suspense>; }
