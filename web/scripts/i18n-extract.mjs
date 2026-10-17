// Generates locales/en.json from t("key", "English default") calls, plus the dynamic key families below.
import fs from "node:fs";
import path from "node:path";

const roots = ["app", "components", "lib"];
const files = [];
const walk = (d) => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) walk(p); else if (/\.tsx?$/.test(f.name)) files.push(p); } };
roots.forEach(walk);

const re = /\bt\(\s*"([A-Za-z0-9_.]+)"\s*,\s*"((?:[^"\\]|\\.)*)"/g;
const out = {};
for (const f of files) {
  const src = fs.readFileSync(f, "utf8");
  for (const m of src.matchAll(re)) {
    const val = JSON.parse(`"${m[2]}"`);
    if (out[m[1]] && out[m[1]] !== val) console.warn(`! key ${m[1]} has two different defaults:\n   ${out[m[1]]}\n   ${val}`);
    out[m[1]] ??= val;
  }
}
const fam = {
  work: { delivery: "Delivery", driver: "Driver / cab", domestic: "Domestic work", construction: "Construction", daily_wage: "Daily wage", street_vendor: "Street vendor", other: "Other" },
  track: { saved: "Saved", documents_ready: "Documents ready", applied: "I applied", received: "I received it", rejected: "Rejected" },
  gi: { unpaid_wages: "Unpaid wages", incentive: "Missing incentive", deduction: "Unexplained deduction", deactivation: "Platform deactivation", contractor: "Contractor dispute" },
  gs: { draft: "Draft", ready: "Ready to submit", submitted: "Submitted", resolved: "Resolved" },
  ik: { extra_payment: "Extra payment I got", benefit_received: "Benefit I received", expense_avoided: "Expense I avoided", scheme_discovered: "Schemes discovered", application_started: "Applications started", complaint_submitted: "Complaints submitted", complaint_resolved: "Complaints resolved", document_completed: "Documents completed" },
  dt: { challan: "Challan", loan_agreement: "Loan agreement", contract: "Contract", payout: "Payout record", notice: "Notice", other: "Document" },
  risk: { risk_interest: "High interest or charges mentioned - work out the real yearly rate before signing.", risk_penalty: "A penalty or fine clause - check how much and when it applies.", risk_terminate: "Work can end without notice - ask for the notice period and reasons in writing.", risk_deduct: "Money can be deducted from your pay - ask for exact amounts and reasons.", risk_nonrefund: "Non-refundable payment - do not pay before reading the full terms.", risk_advance: "Advance or deposit - get a receipt and a written refund policy." },
  scheme: { eshram: "e-Shram registration", pmsym: "PM-SYM pension", apy: "Atal Pension Yojana", pmsby: "PM Suraksha Bima (accident)", pmjjby: "PM Jeevan Jyoti Bima (life)", bocw: "Construction workers welfare board" },
  q: { state: "State", age: "Age", work_type: "Type of work", monthly_income: "Monthly income", epfo_member: "EPFO/ESIC membership", nps_member: "NPS coverage", income_tax_payer: "Income-tax status", govt_pension: "Other government pension", has_bank: "Bank account", street_vendor: "Street vendor" },
  "opp.conf": { low: "Confidence: low", medium: "Confidence: medium", high: "Confidence: high" },
};
for (const [p, kv] of Object.entries(fam)) for (const [k, v] of Object.entries(kv)) out[`${p}.${k}`] = v;
const sorted = Object.fromEntries(Object.entries(out).sort(([a], [b]) => a.localeCompare(b)));
fs.writeFileSync("locales/en.json", JSON.stringify(sorted, null, 1) + "\n");
console.log(Object.keys(sorted).length, "keys written to locales/en.json");
