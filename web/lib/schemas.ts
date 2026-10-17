import { z } from "zod";

const num = (label = "Required") => z.number({ required_error: label, invalid_type_error: label }).min(0, "Must be 0 or more");
/** react-hook-form `setValueAs` for numeric inputs: empty string -> undefined so Zod can say "Required". */
export const toNum = (v: unknown) => (v === "" || v === null || v === undefined ? undefined : Number(v));

export const shiftSchema = z.object({
  platform: z.string().trim().min(1, "Required").max(40),
  day: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pick a date"),
  hours: num().max(24, "Maximum 24"),
  start_hour: z.number().int().min(0).max(23).optional(),
  gross: num(), commission: num(), deductions: num(), incentive: num(), fuel: num(), other_expenses: num(),
  promised: z.number().min(0).optional(), received: z.number().min(0).optional(),
});
export type ShiftForm = z.infer<typeof shiftSchema>;

export const tripSchema = z.object({
  fare: num(), distance_km: num(), time_min: z.number({ required_error: "Required", invalid_type_error: "Required" }).gt(0, "Must be more than 0"),
  return_km: num(), commission_pct: num().max(100), tolls: num(), other_expenses: num(),
  mileage_kmpl: z.number({ required_error: "Required", invalid_type_error: "Required" }).gt(0, "Must be more than 0"),
  fuel_price: z.number({ required_error: "Required", invalid_type_error: "Required" }).gt(0, "Must be more than 0"),
  wear_per_km: num(),
});
export type TripForm = z.infer<typeof tripSchema>;

export const diarySchema = z.object({
  day: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pick a date"), employer: z.string().trim().max(80), work: z.string().trim().max(120),
  hours: num().max(24), promised: num(), received: num(),
});
export type DiaryForm = z.infer<typeof diarySchema>;

export const grievanceSchema = z.object({
  issue: z.enum(["unpaid_wages", "incentive", "deduction", "deactivation", "contractor"]),
  name: z.string().trim().min(2, "Required").max(80), company: z.string().trim().min(2, "Required").max(80),
  incident_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pick a date"), amount: num(),
  details: z.string().trim().min(5, "Please describe what happened").max(1000),
  desired: z.string().trim().max(200).optional(),
});
export type GrievanceForm = z.infer<typeof grievanceSchema>;

export const impactSchema = z.object({
  kind: z.string().min(1), amount: num(), basis: z.enum(["user_reported", "estimated"]), note: z.string().max(200).optional(),
});
export type ImpactForm = z.infer<typeof impactSchema>;

export const expenseSchema = z.object({ category: z.string().trim().min(1, "Required").max(30), amount: z.number({ required_error: "Required", invalid_type_error: "Required" }).gt(0, "Must be more than 0") });
export type ExpenseForm = z.infer<typeof expenseSchema>;
