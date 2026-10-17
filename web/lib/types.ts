export type DataSource = "demo" | "user" | "empty" | "estimate";
export interface Agg { gross: number; expenses: number; net: number; hours: number; net_per_hour: number | null }
export interface Pending { type: "scheme" | "document_expiry" | "grievance"; id: string | number; status?: string; due?: string | null; days_left?: number; company?: string; follow_up_on?: string }
export interface Dashboard {
  data_source: DataSource; today: Agg; week: Agg; series: { day: string; gross: number; expenses: number; net: number }[];
  ai_summary: string; summary_basis: string; pending: Pending[];
}
export interface Discrepancy { expected_payout: number; received: number | null; promised: number | null; shortfall_vs_calculated: number | null; shortfall_vs_promised: number | null; status: "unknown" | "matches" | "possible_discrepancy" }
export interface ShiftRow { id: number; day: string; platform: string; hours: number; start_hour: number | null; gross: number; commission: number; deductions: number; incentive: number; fuel: number; other_expenses: number; promised: number | null; received: number | null; source: string; take_home: number; discrepancy: Discrepancy }
export interface ShiftInput { user: string; day?: string; platform: string; hours: number; start_hour?: number | null; gross: number; commission: number; deductions: number; incentive: number; fuel: number; other_expenses: number; promised?: number | null; received?: number | null; source?: string }
export interface ProofResult {
  validated_record: Record<string, unknown>;
  calculation: { platform_total: number; take_home: number } & Discrepancy;
  explanation: { code: "possible_discrepancy" | "no_discrepancy" | "insufficient_data"; shortfall: number; message: string; disclaimer: string };
  shift_id: number | null; evidence: { label: string; detail: string }[];
  grievance: { id: number; status: string; letter: string; letter_local: string; escalation: EscalationStep[] } | null;
  next_step: { message: string; ladder_step: string } | null; tracking: { how: string } | null;
}
export interface EscalationStep { id: string; to: string; note: string; where: string }
export interface Grievance { id: number; kind: string; company: string; status: "draft" | "ready" | "submitted" | "resolved"; letter: string; letter_local: string; timeline: { day: string; event: string }[]; evidence: string[]; escalation: EscalationStep[]; follow_ups: string[]; submitted_on: string | null; note: string; created: string; facts: Record<string, unknown> }
export interface TripResult { net_profit: number; net_per_hour: number; net_per_km: number; cost: number; cost_per_km: number; breakeven_fare: number | null; fuel_cost: number; wear_cost: number; commission: number; verdict: "accept" | "marginal" | "skip"; assumptions: string[]; vs_history: { your_average_net_per_hour: number; difference_per_hour: number; better_than_average: boolean } | null }
export interface Opportunity { category: "earn_more" | "save_money" | "rights_benefits"; title: string; why: string; evidence: string[]; impact: { value?: number; value_per_hour?: number; basis: string; note: string } | null; confidence: "none" | "low" | "medium" | "high"; effort: string; next: { label: string; href: string } }
export interface SchemeCard {
  id: string; title: string; authority: string; summary: string; how_to_apply: string; benefits: string[]; exclusions: string[]; documents: string[]; steps: string[];
  apply_url: string; channels: string[]; sources: { title: string; url: string; authority: string; last_verified: string | null }[]; last_verified: string | null;
  verification: "verified" | "unverified_seed"; text_language: string;
  state: "potentially_relevant" | "more_info_needed" | "appears_ineligible" | "requires_official_confirmation"; state_label: string; why_qualify: string[]; why_not: string[]; missing: string[];
}
export interface HaqQuestion { id: string; type: "text" | "number" | "select" | "bool"; options: string[] | null; label: string }
export interface TrackerItem { scheme_id: string; title: string; status: string; reminder: string | null; checklist: Record<string, boolean>; note: string }
export interface Impact {
  money: { verified: number; user_reported: number; estimated: number }; money_by_kind_user_reported: Record<string, number>; counts: Record<string, number>;
  entries: { id: number; day: string; kind: string; amount: number; basis: "estimated" | "user_reported" | "verified"; note: string }[]; notes: string[]; data_source: DataSource;
}
export interface DocAnalysis { doc_type: string; dates: string[]; amounts: number[]; deadlines: string[]; fees: string[]; obligations: string[]; risks: { key: string; snippet: string }[]; checklist: string[]; ai_summary: string | null; ai_summary_available: boolean; disclaimer: string; note: string }
export interface ChatReply { reply: string; intent: string; lang: string; sources: { title: string; url: string; last_verified?: string | null }[]; escalate: boolean }
export interface LanguageInfo { code: string; name: string; speech: string }
