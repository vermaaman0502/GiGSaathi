"use client";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useApp } from "@/app/providers";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/misc";
import { Haq } from "@/components/features/haq";
import { Docs } from "@/components/features/docs";
import { GrievanceBuilder } from "@/components/features/grievance";
import { Safety } from "@/components/features/safety";

function Inner() {
  const { t } = useApp();
  const router = useRouter();
  const tab = useSearchParams().get("tab") || "schemes";
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t("nav.rights", "Rights & Safety")}</h1>
      <Tabs value={tab} onValueChange={(v) => router.replace(`/rights?tab=${v}`)}>
        <TabsList aria-label={t("nav.rights", "Rights & Safety")}>
          <TabsTrigger value="schemes">{t("rt.schemes", "Welfare schemes")}</TabsTrigger><TabsTrigger value="docs">{t("rt.docs", "Documents")}</TabsTrigger>
          <TabsTrigger value="grievance">{t("rt.grievance", "Complaints")}</TabsTrigger><TabsTrigger value="safety">{t("rt.safety", "Safety")}</TabsTrigger>
        </TabsList>
        <TabsContent value="schemes"><Haq /></TabsContent>
        <TabsContent value="docs"><Docs /></TabsContent>
        <TabsContent value="grievance"><GrievanceBuilder /></TabsContent>
        <TabsContent value="safety"><Safety /></TabsContent>
      </Tabs>
    </div>
  );
}
export default function Page() { return <Suspense fallback={null}><Inner /></Suspense>; }
