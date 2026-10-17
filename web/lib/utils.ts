import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
export const rupees = (n: number | null | undefined, digits = 0) =>
  n === null || n === undefined ? "—" : "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
export const today = () => new Date().toISOString().slice(0, 10);
