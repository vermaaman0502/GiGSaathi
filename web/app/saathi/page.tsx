"use client";
import { Suspense } from "react";
import { useApp } from "@/app/providers";
import { Chat } from "@/components/features/chat";

export default function Page() {
  const { t } = useApp();
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">{t("nav.saathi", "Saathi AI")}</h1>
      <Suspense fallback={null}><Chat /></Suspense>
    </div>
  );
}
