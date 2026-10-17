"use client";
import { useState } from "react";
import { CloudSun, MapPin } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/misc";
import { ReadAloud } from "@/components/voice";

/** Consent-based weather/heat alert. Says plainly when location or the weather service is unavailable. */
export function WeatherCard() {
  const { t, lang, consent, setConsent } = useApp();
  const [w, setW] = useState<Awaited<ReturnType<typeof api.weather>> | null>(null);
  const [err, setErr] = useState("");
  const check = () => {
    setErr(""); setW(null);
    if (!navigator.geolocation) { setErr(t("loc.unsupported", "Location is not available on this device.")); return; }
    navigator.geolocation.getCurrentPosition(
      (p) => api.weather(p.coords.latitude, p.coords.longitude, lang).then(setW).catch(() => setErr(t("weather.unavailable", "Weather service is unavailable right now. No alert can be shown."))),
      () => setErr(t("loc.denied", "Location permission was denied. No weather alert can be shown.")), { timeout: 8000 });
  };
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><CloudSun className="size-4" />{t("weather.title", "Weather & heat alert")}</CardTitle></CardHeader>
      <CardContent className="space-y-2 text-sm">
        {!consent.location ? (
          <Alert variant="warning" title={t("loc.consent.title", "Allow location?")}>
            {t("loc.consent.body", "Your location is used once to fetch today's weather. It is not stored.")}
            <div className="mt-2"><Button size="sm" onClick={() => { setConsent("location", true); check(); }}><MapPin />{t("common.allow", "Allow")}</Button></div>
          </Alert>
        ) : <Button size="sm" onClick={check}><MapPin />{t("weather.check", "Check today's weather")}</Button>}
        {err && <Alert variant="warning">{err}</Alert>}
        {w && <Alert variant={w.heat_alert || w.rain_alert ? "warning" : "info"} title={w.available ? `${t("weather.source", "Source")}: ${w.source}` : undefined}>{w.message}<ReadAloud text={w.message} /></Alert>}
      </CardContent>
    </Card>
  );
}
