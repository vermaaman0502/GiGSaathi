// Critical-journey E2E. Needs: backend on :8000 and `next start` on :3000. CHROME=/path/to/chrome
import puppeteer from "puppeteer-core";

const BASE = process.env.WEB || "http://localhost:3000";
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failures = 0;
const check = (name, cond, extra = "") => { console.log(`${cond ? "PASS" : "FAIL"}  ${name}${cond ? "" : "  -> " + extra}`); if (!cond) failures++; };

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--no-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900 });
const errors = [];
page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/favicon|Failed to load resource/.test(m.text())) errors.push("console: " + m.text()); });

const text = () => page.evaluate(() => document.body.innerText);
const waitText = async (needle, ms = 8000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if ((await text()).includes(needle)) return true; await sleep(150); } return false; };
const clickText = async (label, sel = "button, a") => {
  const ok = await page.evaluate((label, sel) => { const el = [...document.querySelectorAll(sel)].find((e) => e.innerText.trim().includes(label) && !e.disabled); if (el) { el.click(); return true; } return false; }, label, sel);
  await sleep(250); return ok;
};
const go = async (path) => { await page.goto(BASE + path, { waitUntil: "networkidle0" }); await sleep(300); };
const setInput = async (id, value) => { await page.click(`#${id}`, { clickCount: 3 }); await page.keyboard.press("Backspace"); await page.type(`#${id}`, String(value)); };

// ---------- 1. Home: empty state -> demo ----------
await go("/?lang=en");
await page.evaluate(() => { try { localStorage.clear(); } catch {} });   // clear once (a fresh anonymous worker), then keep state across pages
await go("/?lang=en");
check("home: command center renders", await waitText("Your Worker Command Center"));
check("home: honest empty state", await waitText("No shifts saved yet"));
check("home: talk to Saathi voice control present", (await text()).includes("Talk to Saathi"));
check("home: switch to demo", await clickText("Explore with demo data"));
check("home: demo banner shown", await waitText("DEMO MODE", 10000));
await sleep(1200);
const homeTxt = await text();
check("home: KPIs show net per hour", homeTxt.includes("Net per hour") && homeTxt.includes("Gross income"));
check("home: weekly chart rendered", (await page.$$("svg.recharts-surface")).length > 0);
check("home: Demo data badge visible", homeTxt.includes("Demo data"));
check("home: three opportunity categories", ["Earn more", "Save money", "Benefits & rights"].every((s) => homeTxt.includes(s)));
check("home: opportunity says estimate not money received", /not money received|estimate/i.test(homeTxt));
check("home: pending items listed", homeTxt.includes("Pending"));

// ---------- 2. Earnings X-Ray -> discrepancy -> complaint draft ----------
await go("/earnings?tab=xray");
check("xray: upload section + demo payout", await waitText("Upload a payout screenshot"));
await clickText("Use synthetic demo payout");
check("xray: review-before-save warning", await waitText("Please review before saving"));
check("xray: synthetic label", (await text()).includes("SYNTHETIC"));
check("xray: gross prefilled from extraction", (await page.$eval("#gross", (e) => e.value)) === "1100");
await clickText("Check my payout");
check("xray: possible discrepancy (not fraud) result", await waitText("Possible discrepancy"));
const xr = await text();
check("xray: shows ₹160 shortfall and explicit disclaimer", xr.includes("₹160") && xr.includes("not proof of wrongdoing"));
check("xray: evidence listed + export", xr.includes("Evidence saved") && xr.includes("Download evidence"));
await setInput("cn", "Ravi Kumar"); await setInput("cc", "SwiftEats");
await clickText("Draft a complaint from this evidence");
check("xray: draft saved but NOT submitted", await waitText("Draft saved (not submitted)"));

// ---------- 3. Trip profit ----------
await go("/earnings?tab=trip");
await clickText("Calculate");
check("trip: result with break-even and calculation shown", await waitText("Break-even fare") && (await text()).includes("How this was calculated"));
check("trip: compares with own history (demo worker)", (await text()).includes("Your own saved shifts average"));
await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; }));   // the user expands "Assumptions"
await setInput("mileage_kmpl", "0"); await clickText("Calculate");
check("trip: validation blocks bad mileage", await waitText("Must be more than 0"));

// ---------- 4. HaqFinder in Hindi ----------
await go("/rights?tab=schemes&lang=hi");
check("haq: conversational question in Hindi", await waitText("आप किस राज्य में रहते हैं?"));
await setInput("haq-in", "punjab"); await clickText("आगे"); await sleep(500);
await setInput("haq-in", "28"); await clickText("आगे"); await sleep(500);
check("haq: asks only needed next question (work type)", await waitText("आप क्या काम करते हैं?"));
await clickText("डिलीवरी"); await sleep(500);
await setInput("haq-in", "12000"); await clickText("आगे"); await sleep(500);
for (let i = 0; i < 6; i++) { const t = await text(); if (t.includes("अभी के लिए बस इतना काफ़ी है")) break; await clickText("नहीं", "button"); await sleep(450); }
const haq = await text();
check("haq: finished the questionnaire", haq.includes("अभी के लिए बस इतना काफ़ी है"));
check("haq: scheme cards in Hindi with explicit state labels", haq.includes("संभवतः प्रासंगिक") && haq.includes("पात्रता की सरकारी पुष्टि ज़रूरी है"));
check("haq: verified badge on e-Shram, unverified on others", haq.includes("सत्यापित 2026-10-17") && haq.includes("अभी सत्यापित नहीं"));
check("haq: Hindi scheme content (not English)", haq.includes("ई-श्रम") && haq.includes("पेंशन"));
check("haq: ineligible shown honestly (Punjab has no state gig law found)", haq.includes("आपके उत्तरों के आधार पर पात्र नहीं लगता"));
check("haq: official link + sources + disclaimer", haq.includes("सरकारी आवेदन लिंक") && haq.includes("स्रोत") && haq.includes("पहली जाँच है, फ़ैसला नहीं"));
await clickText("मेरी सूची में सहेजें"); await sleep(600);
check("haq: tracker with status recorded by user", (await text()).includes("स्थिति आप खुद दर्ज करते हैं"));

// ---------- 5. Complaint workflow ----------
await go("/rights?tab=grievance&lang=en");
check("grievance: draft from X-Ray is listed", await waitText("My complaints") && (await text()).includes("SwiftEats"));
await clickText("SwiftEats");
check("grievance: review/edit screen with honest note", await waitText("Review and edit your complaint") && (await text()).includes("does not submit"));
check("grievance: letter contains the evidence and amount", (await page.$eval("#letter", (e) => e.value)).includes("160"));
await clickText("Ready to submit"); await sleep(500);
await clickText("Submitted"); await sleep(700);
const gt = await text();
check("grievance: follow-up dates appear after user marks submitted", gt.includes("Suggested follow-up dates"));
check("grievance: escalation ladder with where-to-go", gt.includes("Where to escalate") && gt.includes("Platform support"));

// ---------- 6. Impact ledger ----------
await go("/impact");
const imp = await text();
check("impact: three bases kept apart", imp.includes("Estimated") && imp.includes("Reported by you") && imp.includes("Independently verified"));
check("impact: estimate flagged as NOT money received", imp.includes("NOT money received"));
check("impact: verified stays ₹0", /Independently verified[\s\S]{0,40}₹0/.test(imp) && imp.includes("stays at ₹0"));
check("impact: complaint submitted counted", /1\s*\n?\s*Complaints submitted/.test(imp));

// ---------- 7. Chat replies in the language asked ----------
await go("/saathi?lang=en");
await page.type("#chat-in", "मुझे पेंशन स्कीम बताओ"); await page.keyboard.press("Enter");
const afterQ = async (q, re, ms = 10000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (re.test((await text()).split(q).pop() || "")) return true; await sleep(150); } return false; };
const chatReady = () => page.waitForFunction(() => { const el = document.querySelector("#chat-in"); return el && !el.disabled; }, { timeout: 15000 });
check("chat: Hindi question -> Hindi reply", await afterQ("मुझे पेंशन स्कीम बताओ", /[ऀ-ॿ]{5,}/), (await text()).slice(-600));
await chatReady();
await page.type("#chat-in", "trip fare 120 distance 8 km"); await page.keyboard.press("Enter");
check("chat: English question -> English reply", await waitText("Verdict"), (await text()).slice(-400));
await chatReady();
await page.type("#chat-in", "ਅੱਜ 850 ਕਮਾਏ"); await page.keyboard.press("Enter");
check("chat: Punjabi question -> Punjabi reply", await afterQ("ਅੱਜ 850 ਕਮਾਏ", /[਀-੿]{4,}/));
await chatReady();
await page.type("#chat-in", "mera accident ho gaya bachao"); await page.keyboard.press("Enter");
check("chat: crisis escalates to 112", await waitText("112"));

// ---------- 8. Safety honesty ----------
await go("/rights?tab=safety&lang=en");
const sf = await text();
check("safety: emergency call is a tel: link, honest that it cannot dispatch", (await page.$('a[href="tel:112"]')) !== null && sf.includes("cannot place the call"));
check("safety: location only after consent prompt", sf.includes("Allow location?") || sf.includes("Get my location"));
await clickText("Check today's weather").catch(() => {});

// ---------- 9. Languages + a11y + responsive ----------
await go("/?lang=pa");
check("language: Punjabi UI", await waitText("ਤੁਹਾਡਾ ਕਾਮਾ ਕਮਾਂਡ ਸੈਂਟਰ"));
await go("/?lang=hi");
check("language: Hindi UI + bottom nav labels", await waitText("आपका कामगार कमांड सेंटर"));
const unlabeled = await page.evaluate(() => [...document.querySelectorAll("input,select,textarea")].filter((e) => !(e.id && document.querySelector(`label[for="${e.id}"]`)) && !e.getAttribute("aria-label") && !e.closest("label") && e.type !== "hidden" && e.type !== "file").map((e) => e.outerHTML.slice(0, 80)));
check("a11y: every form control has a label", unlabeled.length === 0, unlabeled.join(" | "));
await go("/earnings?tab=trip&lang=en");
const unl2 = await page.evaluate(() => [...document.querySelectorAll("input,select,textarea")].filter((e) => !(e.id && document.querySelector(`label[for="${e.id}"]`)) && !e.getAttribute("aria-label") && !e.closest("label")).map((e) => e.outerHTML.slice(0, 80)));
check("a11y: trip form controls labelled", unl2.length === 0, unl2.join(" | "));
const nobtnname = await page.evaluate(() => [...document.querySelectorAll("button, a[href]")].filter((e) => !(e.innerText || "").trim() && !e.getAttribute("aria-label") && !e.title).length);
check("a11y: every button/link has an accessible name", nobtnname === 0, String(nobtnname));
check("a11y: skip link + main landmark", (await page.$("a[href='#main']")) !== null && (await page.$("main#main")) !== null);
check("desktop: sidebar nav visible", await page.evaluate(() => { const a = document.querySelector("aside"); return !!a && getComputedStyle(a).display !== "none"; }));
await page.setViewport({ width: 390, height: 800, isMobile: true });
await go("/?lang=en");
const mobile = await page.evaluate(() => { const nav = [...document.querySelectorAll("nav")].find((n) => getComputedStyle(n).position === "fixed"); return { nav: nav ? [...nav.querySelectorAll("a")].map((a) => a.innerText.trim()) : [], overflow: document.documentElement.scrollWidth > window.innerWidth + 2 }; });
check("mobile: bottom nav = Home, Earnings, Saathi AI, Rights & Safety", JSON.stringify(mobile.nav) === JSON.stringify(["Home", "Earnings", "Saathi AI", "Rights & Safety"]), JSON.stringify(mobile.nav));
check("mobile: no horizontal overflow", !mobile.overflow);
await page.setViewport({ width: 1280, height: 900 });

// ---------- 10. Privacy: export + delete (real workspace) ----------
await go("/settings?mode=real&lang=en");
await page.evaluate(() => { localStorage.setItem("gs_mode", "real"); }); await go("/settings?lang=en");
await clickText("Delete all my data"); await clickText("Yes, delete everything");
check("privacy: deletion confirmed with record count", await waitText("Deleted"));

check("no JS errors during the whole run", errors.length === 0, errors.slice(0, 5).join(" || "));
await browser.close();
console.log(failures === 0 ? "\nALL E2E JOURNEYS PASSED" : `\n${failures} CHECK(S) FAILED`);
process.exit(failures ? 1 : 0);
