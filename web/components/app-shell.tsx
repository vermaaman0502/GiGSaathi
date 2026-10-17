"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Bell, Heart, Home, IndianRupee, MessageCircle, Settings, ShieldCheck, Sprout, FlaskConical, User } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { FULL_UI } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { LanguageInfo, Pending } from "@/lib/types";
import { Select } from "@/components/ui/form-controls";
import { Skeleton } from "@/components/ui/misc";

const STATIC_LANGS: LanguageInfo[] = [
  { code: "en", name: "English", speech: "en-IN" }, { code: "hi", name: "हिन्दी", speech: "hi-IN" }, { code: "pa", name: "ਪੰਜਾਬੀ", speech: "pa-IN" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t, lang, setLang, mode, setMode, userId, refreshKey, ready } = useApp();
  const path = usePathname();
  const [langs, setLangs] = useState<LanguageInfo[]>(STATIC_LANGS);
  const [pending, setPending] = useState<Pending[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => { api.languages().then((r) => setLangs(r.languages.filter((l) => l.code !== "hinglish" || true))).catch(() => {}); }, []);
  useEffect(() => {
    if (!userId) return;
    api.dashboard(userId, lang).then((d) => setPending(d.pending)).catch(() => setPending([]));
  }, [userId, lang, refreshKey]);

  const main = [
    { href: "/", icon: Home, label: t("nav.home", "Home") },
    { href: "/earnings", icon: IndianRupee, label: t("nav.earnings", "Earnings") },
    { href: "/saathi", icon: MessageCircle, label: t("nav.saathi", "Saathi AI") },
    { href: "/rights", icon: ShieldCheck, label: t("nav.rights", "Rights & Safety") },
  ];
  const more = [
    { href: "/impact", icon: Sprout, label: t("nav.impact", "Impact") },
    { href: "/demo", icon: FlaskConical, label: t("nav.demo", "Demo walkthrough") },
    { href: "/settings", icon: Settings, label: t("nav.settings", "Settings & privacy") },
  ];
  const active = (h: string) => (h === "/" ? path === "/" : path.startsWith(h));
  const link = (n: { href: string; icon: typeof Home; label: string }) => (
    <Link key={n.href} href={n.href} aria-current={active(n.href) ? "page" : undefined}
      className={cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold", active(n.href) ? "bg-primary text-primary-foreground" : "hover:bg-accent")}>
      <n.icon className="size-5" />{n.label}
    </Link>
  );

  return (
    <div className="min-h-screen md:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-card focus:p-3">{t("a11y.skip", "Skip to content")}</a>
      <aside className="no-print hidden w-64 shrink-0 flex-col gap-1 border-r bg-card p-4 md:flex" aria-label="Main">
        <Link href="/" className="mb-4 flex items-center gap-2 text-xl font-bold text-primary"><Heart className="size-6" fill="currentColor" />GigSaathi</Link>
        <nav className="flex flex-col gap-1">{main.map(link)}<hr className="my-2" />{more.map(link)}</nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="no-print sticky top-0 z-20 flex items-center gap-2 border-b bg-card/95 px-4 py-2 backdrop-blur">
          <Link href="/" className="flex items-center gap-1 font-bold text-primary md:hidden"><Heart className="size-5" fill="currentColor" />GigSaathi</Link>
          <div className="ml-auto flex items-center gap-2">
            <label className="sr-only" htmlFor="lang">{t("ui.language", "Language")}</label>
            <Select id="lang" value={lang} onChange={(e) => setLang(e.target.value)} className="h-10 w-auto max-w-40">
              {langs.map((l) => <option key={l.code} value={l.code}>{l.name}{FULL_UI.includes(l.code) ? "" : " (β)"}</option>)}
            </Select>
            <div className="relative">
              <button aria-label={t("nav.notifications", "Notifications")} aria-expanded={open} onClick={() => setOpen(!open)} className="relative grid size-10 place-items-center rounded-lg border bg-card hover:bg-accent">
                <Bell className="size-5" />{pending.length > 0 && <span className="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">{pending.length}</span>}
              </button>
              {open && (
                <div role="dialog" aria-label={t("nav.notifications", "Notifications")} className="absolute right-0 mt-2 w-72 rounded-xl border bg-card p-3 shadow-lg">
                  {pending.length === 0 ? <p className="text-sm text-muted-foreground">{t("notif.none", "Nothing pending.")}</p> :
                    <ul className="space-y-2 text-sm">{pending.map((p, i) => (
                      <li key={i} className="rounded-lg bg-secondary p-2">
                        <b>{p.type === "scheme" ? t("notif.scheme", "Scheme") : p.type === "grievance" ? t("notif.grievance", "Complaint") : t("notif.doc", "Document expiry")}</b>{" "}
                        {String(p.id)} {p.status ? `· ${p.status}` : ""} {p.due ? `· ${p.due}` : ""} {p.follow_up_on ? `· follow up ${p.follow_up_on}` : ""}
                      </li>))}</ul>}
                </div>
              )}
            </div>
            <Link href="/settings" aria-label={t("nav.profile", "Profile & privacy")} className="grid size-10 place-items-center rounded-lg border bg-card hover:bg-accent"><User className="size-5" /></Link>
          </div>
        </header>
        {mode === "demo" && (
          <div role="status" className="no-print flex flex-wrap items-center justify-between gap-2 bg-warning px-4 py-2 text-sm font-semibold text-warning-foreground">
            <span>{t("demo.banner", "DEMO MODE — all data is synthetic. Nothing here is a real worker record, payment or submission.")}</span>
            <button onClick={() => setMode("real")} className="underline">{t("demo.exit", "Switch to my data")}</button>
          </div>
        )}
        <main id="main" className="mx-auto w-full max-w-5xl flex-1 p-4 pb-28 md:pb-8">
          {/* pages need the device id + saved language, which only exist after the first client effect */}
          {ready && userId ? children : <div className="space-y-3" aria-busy="true"><Skeleton className="h-24" /><Skeleton className="h-40" /><Skeleton className="h-40" /></div>}
        </main>
        <nav className="no-print fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t bg-card md:hidden" aria-label="Main">
          {main.map((n) => (
            <Link key={n.href} href={n.href} aria-current={active(n.href) ? "page" : undefined}
              className={cn("flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold", active(n.href) ? "text-primary" : "text-muted-foreground")}>
              <n.icon className="size-6" />{n.label}
            </Link>))}
        </nav>
      </div>
    </div>
  );
}
