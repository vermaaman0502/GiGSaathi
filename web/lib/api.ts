import type * as T from "./types";

export const API = (process.env.NEXT_PUBLIC_API_URL || "https://gigsaathi-silk.vercel.app").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

// Identical GETs fired at the same moment (e.g. the shell and the page both loading the dashboard) share one request.
const inflight = new Map<string, Promise<unknown>>();

function req<R>(path: string, init?: RequestInit): Promise<R> {
  if (init?.method && init.method !== "GET") return send<R>(path, init);
  const hit = inflight.get(path);
  if (hit) return hit as Promise<R>;
  const p = send<R>(path, init).finally(() => inflight.delete(path));
  inflight.set(path, p);
  return p;
}

async function send<R>(path: string, init?: RequestInit): Promise<R> {
  let res: Response;
  try {
    // only requests with a JSON body declare a content-type: a header-less GET is a "simple" request and skips the CORS preflight
    const headers = init?.body ? { "content-type": "application/json", ...(init.headers || {}) } : init?.headers;
    res = await fetch(API + path, { ...init, headers });
  } catch {
    throw new ApiError("offline", 0);
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = (body as { detail?: unknown }).detail;
    if (res.status === 429) throw new ApiError("Too many requests - please wait a moment and try again.", 429);
    throw new ApiError(typeof d === "string" ? d : Array.isArray(d) ? "Please check the highlighted fields" : "Request failed", res.status);
  }
  return body as R;
}
const post = <R>(p: string, b: unknown) => req<R>(p, { method: "POST", body: JSON.stringify(b) });
const patch = <R>(p: string, b: unknown) => req<R>(p, { method: "PATCH", body: JSON.stringify(b) });

export const api = {
  languages: () => req<{ languages: T.LanguageInfo[] }>("/api/languages"),
  dashboard: (u: string, lang: string) => req<T.Dashboard>(`/api/dashboard/${u}?lang=${lang}`),
  addShift: (b: T.ShiftInput) => post<{ id: number }>("/api/shifts", b),
  shifts: (u: string, days = 30) => req<{ shifts: T.ShiftRow[] }>(`/api/shifts/${u}?days=${days}`),
  deleteShift: (u: string, id: number) => req<unknown>(`/api/shifts/${u}/${id}`, { method: "DELETE" }),
  proof: (b: Record<string, unknown>) => post<T.ProofResult>("/api/proof-to-action", b),
  extractPayout: (text: string) => post<{ fields: Record<string, unknown>; lines_used: string[]; confidence: string; note: string }>("/api/extract/payout-text", { text }),
  demoPayout: () => req<{ text: string; demo: boolean }>("/api/demo/payout-sample"),
  trip: (b: Record<string, unknown>) => post<T.TripResult>("/api/trip-profit", b),
  shiftInsights: (u: string) => req<{ total_shifts: number; enough_data: boolean; bands: { start: number; end: number; n: number; avg: number; min: number; max: number; show_range: boolean }[]; note: string; generic: { start: number; end: number; score: number }[] | null }>(`/api/shift-insights/${u}`),
  weather: (lat: number, lon: number, lang: string) => req<{ available: boolean; message: string; temp_max_c?: number; rain_prob_pct?: number; heat_alert: boolean; rain_alert: boolean; source: string }>(`/api/weather?lat=${lat}&lon=${lon}&lang=${lang}`),
  incentiveParse: (text: string) => post<{ target_trips: number | null; reward: number | null; deadline_text: string | null; confidence: string; note: string }>("/api/incentive/parse", { text }),
  incentiveProgress: (b: Record<string, unknown>) => post<{ rem: number; per_hr: number; message: string }>("/api/incentive/progress", b),
  compare: (u: string) => req<{ platforms: { platform: string; shifts: number; net: number; net_per_hour: number | null; gross: number; hours: number }[]; enough_data: boolean; note: string }>(`/api/compare/platforms/${u}`),
  skills: (w: string) => req<{ note: string; ideas: { idea: string; cost: number; extra_per_month: string; payback_months: number; support: string; prerequisites: string; time_needed: string }[]; resources: { title: string; url: string }[] }>(`/api/skills?work_type=${w}`),
  leaks: (u: string) => req<{ leaks: { category: string; times: number; total: number; why: string; validate: string }[]; note: string }>(`/api/leaks/${u}`),
  diary: (u: string) => req<{ entries: { id: number; day: string; employer: string; work: string; hours: number; promised: number; received: number }[]; promised_total: number; received_total: number; unpaid_total: number }>(`/api/wage-diary/${u}`),
  addExpense: (b: Record<string, unknown>) => post<{ leaks: unknown[] }>("/api/expenses", b),
  addDiary: (b: Record<string, unknown>) => post<unknown>("/api/wage-diary", b),
  opportunities: (u: string, lang: string) => req<{ items: T.Opportunity[]; data_source: T.DataSource; safety_note: string }>(`/api/opportunities/${u}?lang=${lang}`),
  haqMatch: (answers: Record<string, unknown>, lang: string) => post<{ cards: T.SchemeCard[]; next_questions: T.HaqQuestion[]; note: string }>("/api/haq/match", { answers, lang }),
  track: (b: Record<string, unknown>) => post<{ tracker: Record<string, T.TrackerItem> }>("/api/haq/track", b),
  tracked: (u: string) => req<{ tracker: Record<string, T.TrackerItem> }>(`/api/haq/track/${u}`),
  scheme: (id: string, lang: string) => req<T.SchemeCard>(`/api/haq/scheme/${id}?lang=${lang}`),
  analyzeDoc: (text: string, lang: string) => post<T.DocAnalysis>("/api/document/analyze", { text, lang }),
  addEvidence: (b: Record<string, unknown>) => post<unknown>("/api/evidence", b),
  evidence: (u: string) => req<{ evidence: { id: number; day: string; kind: string; title: string }[] }>(`/api/evidence/${u}`),
  createGrievance: (b: Record<string, unknown>) => post<T.Grievance>("/api/grievances", b),
  grievances: (u: string) => req<{ grievances: T.Grievance[] }>(`/api/grievances/${u}`),
  patchGrievance: (id: number, b: Record<string, unknown>) => patch<T.Grievance>(`/api/grievances/${id}`, b),
  practiceList: (lang: string) => req<{ scenarios: { id: string; title: string }[] }>(`/api/practice/scenarios?lang=${lang}`),
  practiceStart: (scenario: string, lang: string) => post<{ scenario: string; step: number; title: string; npc: string; done: boolean }>("/api/practice/start", { scenario, lang }),
  practiceStep: (scenario: string, step: number, answer: string, lang: string) => post<{ step: number; npc: string | null; done: boolean; feedback: { score: number; max: number; tip: string; checks: Record<string, boolean> } }>("/api/practice/step", { scenario, step, answer, lang }),
  impact: (u: string) => req<T.Impact>(`/api/impact/${u}`),
  addImpact: (b: Record<string, unknown>) => post<T.Impact>("/api/impact", b),
  fatigue: (b: Record<string, unknown>) => post<{ level: string; message: string }>("/api/fatigue", b),
  sos: (lang: string) => req<{ message: string; numbers: Record<string, string> }>(`/api/sos?lang=${lang}`),
  vault: (u: string, lang: string) => req<{ items: { doc_type: string; expiry: string; days_left: number; status: string; message: string }[] }>(`/api/vault/${u}?lang=${lang}`),
  addVault: (b: Record<string, unknown>) => post<unknown>("/api/vault", b),
  chat: (user: string, text: string, prefer: string) => post<T.ChatReply>("/chat", { user, text, lang: "auto", prefer }),
  seedDemo: (u: string) => post<unknown>(`/api/demo/seed/${u}`, {}),
  exportUrl: (u: string) => `${API}/api/export/${u}.csv`,
  exportAll: (u: string) => req<Record<string, unknown[]>>(`/api/user/${u}/export`),
  deleteAll: (u: string) => req<{ deleted_rows: Record<string, number> }>(`/api/user/${u}`, { method: "DELETE" }),
};
