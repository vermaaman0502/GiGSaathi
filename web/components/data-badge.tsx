"use client";
import { Badge } from "@/components/ui/badge";
import { useApp } from "@/app/providers";
import type { DataSource } from "@/lib/types";

/** Makes it explicit whether a number is sample data, an estimate, the user's own data, or user-reported / verified. */
export function DataBadge({ source }: { source: DataSource | "user_reported" | "verified" | "estimated" }) {
  const { t } = useApp();
  const map = {
    demo: ["warning", t("badge.demo", "Demo data")], estimate: ["outline", t("badge.estimate", "Estimate")], estimated: ["outline", t("badge.estimate", "Estimate")],
    user: ["secondary", t("badge.user", "Your data")], empty: ["outline", t("badge.empty", "No data yet")],
    user_reported: ["secondary", t("badge.reported", "Reported by you")], verified: ["default", t("badge.verified", "Verified")],
  } as const;
  const [variant, label] = map[source];
  return <Badge variant={variant as "warning" | "outline" | "secondary" | "default"}>{label}</Badge>;
}
