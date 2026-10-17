"use client";
import { useState } from "react";
import { Download, Trash2 } from "lucide-react";
import { useApp } from "@/app/providers";
import { api } from "@/lib/api";
import { safeDel } from "@/lib/user";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/misc";
import { Select } from "@/components/ui/form-controls";

function Toggle({ id, label, checked, onChange, hint }: { id: string; label: string; checked: boolean; onChange: (b: boolean) => void; hint?: string }) {
  return (
    <label htmlFor={id} className="flex items-start justify-between gap-3 py-2">
      <span><span className="font-medium">{label}</span>{hint && <span className="block text-xs text-muted-foreground">{hint}</span>}</span>
      <input id={id} type="checkbox" role="switch" className="mt-1 size-6" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </label>
  );
}

export default function Settings() {
  const { t, userId, mode, setMode, textSize, setTextSize, contrast, setContrast, dark, setDark, consent, setConsent, refresh } = useApp();
  const [msg, setMsg] = useState("");
  const [confirmDel, setConfirmDel] = useState(false);
  const exportAll = async () => {
    const d = await api.exportAll(userId);
    const url = URL.createObjectURL(new Blob([JSON.stringify(d, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = "gigsaathi-my-data.json"; a.click(); URL.revokeObjectURL(url);
  };
  const del = async () => {
    const r = await api.deleteAll(userId);
    safeDel("gs_outbox"); refresh(); setConfirmDel(false);
    setMsg(t("set.deleted", "Deleted {n} records from the server.", { n: Object.values(r.deleted_rows).reduce((a, b) => a + b, 0) }));
  };
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t("nav.settings", "Settings & privacy")}</h1>
      <Card><CardHeader><CardTitle>{t("set.access", "Accessibility")}</CardTitle></CardHeader><CardContent className="divide-y">
        <div className="py-2"><label htmlFor="ts" className="font-medium">{t("set.textsize", "Text size")}</label>
          <Select id="ts" value={textSize} onChange={(e) => setTextSize(e.target.value)} className="mt-1"><option value="normal">{t("set.t.normal", "Normal")}</option><option value="large">{t("set.t.large", "Large")}</option><option value="xlarge">{t("set.t.xl", "Extra large")}</option></Select></div>
        <Toggle id="hc" label={t("set.contrast", "High contrast")} checked={contrast} onChange={setContrast} />
        <Toggle id="dk" label={t("set.dark", "Dark mode")} checked={dark} onChange={setDark} />
      </CardContent></Card>

      <Card><CardHeader><CardTitle>{t("set.consent", "Permissions you control")}</CardTitle></CardHeader><CardContent className="divide-y">
        <Toggle id="cv" label={t("set.voice", "Voice input")} hint={t("set.voice.hint", "Your device records your voice only while you press the mic. We do not keep recordings.")} checked={consent.voice} onChange={(b) => setConsent("voice", b)} />
        <Toggle id="cl" label={t("set.loc", "Location")} hint={t("set.loc.hint", "Used only when you ask for weather or to share your location. Not stored.")} checked={consent.location} onChange={(b) => setConsent("location", b)} />
      </CardContent></Card>

      <Card><CardHeader><CardTitle>{t("set.demo", "Demo mode")}</CardTitle></CardHeader><CardContent className="space-y-2">
        <p className="text-sm text-muted-foreground">{t("set.demo.hint", "Demo mode uses a separate, synthetic worker. It never mixes with your real records.")}</p>
        <Toggle id="dm" label={t("set.demo.on", "Use demo data")} checked={mode === "demo"} onChange={(b) => setMode(b ? "demo" : "real")} />
      </CardContent></Card>

      <Card><CardHeader><CardTitle>{t("set.privacy", "Your data")}</CardTitle></CardHeader><CardContent className="space-y-3 text-sm">
        <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
          <li>{t("set.p1", "We keep only what the features need: shifts, expenses, saved schemes, complaints and notes you create.")}</li>
          <li>{t("set.p2", "We never ask for OTPs, passwords, UPI PINs or your full Aadhaar number.")}</li>
          <li>{t("set.p3", "Your account is a random token stored on this device. If you clear this browser's data without exporting, you lose access to your records.")}</li>
          <li>{t("set.p4", "Records stay until you delete them here. There is no automatic expiry yet.")}</li>
          <li>{t("set.p5", "Photos you scan are read on your device and are not uploaded.")}</li>
        </ul>
        {msg && <Alert variant="info">{msg}</Alert>}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={exportAll}><Download />{t("set.export", "Download my data")}</Button>
          {!confirmDel ? <Button variant="destructive" onClick={() => setConfirmDel(true)}><Trash2 />{t("set.delete", "Delete all my data")}</Button> :
            <><Button variant="destructive" onClick={del}>{t("set.confirm", "Yes, delete everything")}</Button><Button variant="outline" onClick={() => setConfirmDel(false)}>{t("common.cancel", "Cancel")}</Button></>}
        </div>
        <p className="text-xs text-muted-foreground">{t("set.active", "Active workspace")}: {mode === "demo" ? t("badge.demo", "Demo data") : t("badge.user", "Your data")}</p>
      </CardContent></Card>
    </div>
  );
}
