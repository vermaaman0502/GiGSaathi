"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { AlertOctagon, Ambulance, HeartPulse, MapPin, Phone, Share2 } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { toNum } from "@/lib/schemas";
import { useAsync } from "@/lib/use-async";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/form-controls";
import { Alert } from "@/components/ui/misc";
import { ReadAloud } from "@/components/voice";
import { WeatherCard } from "./weather-card";

const NUMBERS: [string, string, string][] = [["112", "safe.n112", "Emergency (police / fire / ambulance)"], ["108", "safe.n108", "Ambulance"], ["181", "safe.n181", "Women helpline"], ["15100", "safe.n15100", "Free legal aid (NALSA)"], ["1930", "safe.n1930", "Cyber fraud"]];

export function Safety() {
  const { t, lang, userId, consent, setConsent, refreshKey, refresh } = useApp();
  const [loc, setLoc] = useState<{ url: string } | null>(null);
  const [locErr, setLocErr] = useState("");
  const [fat, setFat] = useState<string>("");
  const fatForm = useForm<{ hours_worked: number; hours_slept: number; temp_c: number }>({ defaultValues: { hours_worked: 9, hours_slept: 5, temp_c: 36 } });
  const vault = useAsync(() => api.vault(userId, lang), [userId, lang, refreshKey]);
  const guide = useAsync(() => api.scheme("accident_first_hour", lang), [lang]);
  const vf = useForm<{ doc_type: string; expiry: string }>({ defaultValues: { doc_type: "dl", expiry: "" } });

  const getLocation = () => {
    setLocErr(""); setLoc(null);
    if (!navigator.geolocation) { setLocErr(t("loc.unsupported", "Location is not available on this device.")); return; }
    navigator.geolocation.getCurrentPosition((p) => setLoc({ url: `https://maps.google.com/?q=${p.coords.latitude},${p.coords.longitude}` }),
      () => setLocErr(t("loc.denied2", "Location permission was denied or the GPS is not available. Tell your contact where you are in words.")), { timeout: 10000, enableHighAccuracy: true });
  };
  const shareText = `${t("safe.share.msg", "I need help. My location:")} ${loc?.url ?? ""}`;
  const share = async () => {
    if (!loc) return;
    if (navigator.share) { try { await navigator.share({ text: shareText }); } catch { /* cancelled */ } }
    else window.open(`https://wa.me/?text=${encodeURIComponent(shareText)}`, "_blank", "noopener");
  };

  return (
    <div className="space-y-4">
      <Card className="border-destructive">
        <CardHeader><CardTitle className="flex items-center gap-2 text-destructive"><AlertOctagon className="size-5" />{t("safe.sos", "Emergency")}</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Button asChild variant="destructive" size="lg" className="w-full"><a href="tel:112"><Phone />{t("safe.call112", "Call 112 now")}</a></Button>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">{NUMBERS.slice(1).map(([n, k, d]) => <Button key={n} asChild variant="outline"><a href={`tel:${n}`}><Phone />{n} · {t(k, d)}</a></Button>)}</div>
          <p className="text-xs text-muted-foreground">{t("safe.honest", "These buttons open your phone's dialer. GigSaathi cannot place the call for you or dispatch anyone - you must press call. If your phone has no signal, move to a place with signal or ask someone nearby.")}</p>
          <div className="space-y-2 rounded-lg bg-secondary p-3">
            <p className="font-semibold">{t("safe.loc.title", "Share my location with someone I trust")}</p>
            {!consent.location ? (
              <Alert variant="warning">{t("loc.consent.body2", "Your location is read only when you press the button and is not stored by us.")}
                <div className="mt-2"><Button size="sm" onClick={() => { setConsent("location", true); getLocation(); }}><MapPin />{t("common.allow", "Allow")}</Button></div></Alert>
            ) : <Button size="sm" onClick={getLocation}><MapPin />{t("safe.loc.get", "Get my location")}</Button>}
            {locErr && <Alert variant="warning">{locErr}</Alert>}
            {loc && <div className="space-y-2"><p className="break-all text-xs">{loc.url}</p><Button size="sm" onClick={share}><Share2 />{t("safe.loc.share", "Choose who to send it to")}</Button>
              <p className="text-xs text-muted-foreground">{t("safe.loc.note", "This opens your phone's share menu. Nothing is sent until you pick a contact and press send.")}</p></div>}
          </div>
        </CardContent>
      </Card>

      <WeatherCard />

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><HeartPulse className="size-4" />{t("fat.title", "Fatigue check")}</CardTitle></CardHeader>
        <CardContent>
          <form className="grid gap-3 sm:grid-cols-4" onSubmit={fatForm.handleSubmit(async (v) => { const r = await api.fatigue({ ...v, lang }); setFat(r.message); })}>
            <Field id="fw" label={t("l.hoursw", "Hours worked today")}><Input id="fw" type="number" step="any" {...fatForm.register("hours_worked", { setValueAs: toNum })} /></Field>
            <Field id="fs" label={t("l.slept", "Hours slept last night")}><Input id="fs" type="number" step="any" {...fatForm.register("hours_slept", { setValueAs: toNum })} /></Field>
            <Field id="ft" label={t("l.temp", "Temperature (°C)")}><Input id="ft" type="number" step="any" {...fatForm.register("temp_c", { setValueAs: toNum })} /></Field>
            <div className="flex items-end"><Button type="submit">{t("ui.calc", "Calculate")}</Button></div>
          </form>
          {fat && <Alert className="mt-3" variant="info"><span aria-live="polite">{fat}</span><ReadAloud text={fat} /></Alert>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Ambulance className="size-4" />{t("acc.title", "After an accident: the first hour")}</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          {guide.data && <><p>{guide.data.summary}</p><ReadAloud text={guide.data.summary} /><p className="text-xs text-muted-foreground">{t("acc.note", "General guidance, not medical or legal advice. In an emergency, call 112 / 108 first.")}</p></>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>{t("vault.title", "Licence, RC, insurance and PUC reminders")}</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <form className="flex flex-wrap items-end gap-3" onSubmit={vf.handleSubmit(async (v) => { if (!v.expiry) return; await api.addVault({ user: userId, ...v }); vault.reload(); refresh(); })}>
            <Field id="vd" label={t("vault.doc", "Document")}><Select id="vd" {...vf.register("doc_type")}>{[["dl", t("dt.dl", "Driving licence")], ["rc", "RC"], ["insurance", t("dt.ins", "Insurance")], ["puc", "PUC"]].map(([v, l]) => <option key={v} value={v}>{l}</option>)}</Select></Field>
            <Field id="ve" label={t("l.expiry", "Expiry date")}><Input id="ve" type="date" {...vf.register("expiry")} /></Field>
            <Button type="submit">{t("log.save2", "Save")}</Button>
          </form>
          {vault.data?.items.length === 0 && <Alert variant="info">{t("vault.empty", "No documents saved. Add an expiry date to get a reminder.")}</Alert>}
          <ul className="space-y-1">{vault.data?.items.map((i) => <li key={i.doc_type} className={i.days_left < 0 ? "rounded-lg bg-destructive p-2 text-destructive-foreground" : i.days_left <= 30 ? "rounded-lg bg-warning p-2 text-warning-foreground" : "rounded-lg bg-secondary p-2"}>{i.days_left < 0 ? "⛔ " : i.days_left <= 30 ? "⚠ " : "✅ "}{i.message}</li>)}</ul>
          <p className="text-xs text-muted-foreground">{t("vault.note", "Reminders appear on your home screen and in the bell menu. Push/SMS reminders are not set up yet.")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
