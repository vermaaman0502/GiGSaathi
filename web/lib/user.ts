/** Device-scoped identity. A random 128-bit token acts as the user's secret until real auth (Supabase) is added. */
export const newToken = (prefix: string) => {
  const b = new Uint8Array(16);
  crypto.getRandomValues(b);
  return prefix + Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
};
export const safeGet = (k: string): string | null => { try { return localStorage.getItem(k); } catch { return null; } };
export const safeSet = (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* storage blocked */ } };
export const safeDel = (k: string) => { try { localStorage.removeItem(k); } catch { /* ignore */ } };
