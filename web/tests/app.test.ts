import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import en from "@/locales/en.json";
import hi from "@/locales/hi.json";
import pa from "@/locales/pa.json";
import { translate } from "@/lib/i18n";
import { expenseSchema, grievanceSchema, impactSchema, shiftSchema, toNum, tripSchema } from "@/lib/schemas";
import { browserProvider, getSpeech, providers } from "@/lib/speech";

const PH = /\{(\w+)\}/g;
const ph = (s: string) => [...s.matchAll(PH)].map((m) => m[1]).sort();

describe("i18n", () => {
  it("Hindi and Punjabi cover every English key with the same placeholders", () => {
    for (const [name, d] of [["hi", hi], ["pa", pa]] as const) {
      const missing = Object.keys(en).filter((k) => !(k in d));
      expect(missing, `${name} missing`).toEqual([]);
      expect(Object.keys(d).filter((k) => !(k in en)), `${name} extra`).toEqual([]);
      for (const k of Object.keys(en)) {
        expect(ph((d as Record<string, string>)[k]), `${name}.${k}`).toEqual(ph((en as Record<string, string>)[k]));
        expect((d as Record<string, string>)[k].trim(), `${name}.${k} empty`).not.toBe("");
      }
    }
  });
  it("every t('key', 'default') used in the code exists in en.json", () => {
    const files: string[] = [];
    const walk = (d: string) => fs.readdirSync(d, { withFileTypes: true }).forEach((f) => { const p = path.join(d, f.name); f.isDirectory() ? walk(p) : /\.tsx?$/.test(f.name) && files.push(p); });
    ["app", "components", "lib"].forEach(walk);
    const re = /\bt\(\s*"([A-Za-z0-9_.]+)"\s*,\s*"/g;
    const used = new Set<string>();
    for (const f of files) for (const m of fs.readFileSync(f, "utf8").matchAll(re)) used.add(m[1]);
    expect(used.size).toBeGreaterThan(100);
    expect([...used].filter((k) => !(k in en))).toEqual([]);
  });
  it("translates with variables and falls back to English for other languages", () => {
    expect(translate("hi", "set.deleted", undefined, { n: 3 })).toContain("3");
    expect(translate("ta", "nav.home")).toBe("Home");              // no Tamil UI yet -> English chrome
    expect(translate("pa", "nope.key", "fallback text")).toBe("fallback text");
  });
});

describe("schemas", () => {
  const ok = { platform: "SwiftEats", day: "2026-10-17", hours: 8, gross: 1000, commission: 200, deductions: 0, incentive: 0, fuel: 100, other_expenses: 0 };
  it("accepts a valid shift and rejects bad ones with clear messages", () => {
    expect(shiftSchema.safeParse(ok).success).toBe(true);
    expect(shiftSchema.safeParse({ ...ok, hours: 30 }).success).toBe(false);
    expect(shiftSchema.safeParse({ ...ok, gross: -1 }).success).toBe(false);
    expect(shiftSchema.safeParse({ ...ok, platform: "" }).success).toBe(false);
    expect(shiftSchema.safeParse({ ...ok, gross: undefined }).error?.issues[0].message).toBe("Required");
    expect(shiftSchema.safeParse({ ...ok, day: "17/10/2026" }).success).toBe(false);
  });
  it("toNum turns empty input into undefined so 'Required' shows", () => {
    expect(toNum("")).toBeUndefined(); expect(toNum("12.5")).toBe(12.5); expect(toNum(undefined)).toBeUndefined();
  });
  it("validates trip, grievance, impact and expense forms", () => {
    const trip = { fare: 120, distance_km: 8, time_min: 25, return_km: 4, commission_pct: 20, tolls: 0, other_expenses: 0, mileage_kmpl: 40, fuel_price: 100, wear_per_km: 2 };
    expect(tripSchema.safeParse(trip).success).toBe(true);
    expect(tripSchema.safeParse({ ...trip, mileage_kmpl: 0 }).success).toBe(false);
    expect(tripSchema.safeParse({ ...trip, commission_pct: 120 }).success).toBe(false);
    const g = { issue: "deduction", name: "Ravi", company: "ABC", incident_date: "2026-10-17", amount: 160, details: "Payout was short" };
    expect(grievanceSchema.safeParse(g).success).toBe(true);
    expect(grievanceSchema.safeParse({ ...g, issue: "other" }).success).toBe(false);
    expect(grievanceSchema.safeParse({ ...g, details: "x" }).success).toBe(false);
    expect(impactSchema.safeParse({ kind: "extra_payment", amount: 100, basis: "verified" }).success).toBe(false);   // clients can never claim 'verified'
    expect(impactSchema.safeParse({ kind: "extra_payment", amount: 100, basis: "user_reported" }).success).toBe(true);
    expect(expenseSchema.safeParse({ category: "chai", amount: 0 }).success).toBe(false);
  });
});

describe("speech provider abstraction", () => {
  it("unconfigured providers report unavailable and fail gracefully", () => {
    let reason = "";
    const stop = providers.bhashini.listen("hi", () => {}, (r) => { reason = r; });
    expect(reason).toBe("not_configured"); expect(typeof stop).toBe("function");
    expect(providers.sarvam.canListen()).toBe(false);
  });
  it("falls back to the browser provider and never throws without a browser", () => {
    expect(getSpeech()).toBe(browserProvider);
    expect(browserProvider.canListen()).toBe(false);          // node: no SpeechRecognition
    let reason = ""; browserProvider.listen("hi", () => {}, (r) => { reason = r; });
    expect(reason).toBe("unsupported");
    expect(() => browserProvider.speak("hello", "en")).not.toThrow();
  });
});
