"use client";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { rupees } from "@/lib/utils";

export type BarSeries = { key: string; name: string; color: string };

/** Rupee bar chart. Loaded on demand (see ./index.ts) so Recharts stays out of the first page load. */
export default function Bars({ data, xKey, series, legend = false }: { data: Record<string, unknown>[]; xKey: string; series: BarSeries[]; legend?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
        <XAxis dataKey={xKey} fontSize={12} tickLine={false} axisLine={false} stroke="hsl(var(--muted-foreground))" />
        <YAxis fontSize={12} width={44} tickLine={false} axisLine={false} stroke="hsl(var(--muted-foreground))" />
        <Tooltip formatter={(v) => rupees(Number(v))} cursor={{ fill: "hsl(var(--muted))" }}
          contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", background: "hsl(var(--card))", color: "hsl(var(--card-foreground))" }} />
        {legend && <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />}
        {series.map((s) => <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} radius={[6, 6, 0, 0]} maxBarSize={28} />)}
      </BarChart>
    </ResponsiveContainer>
  );
}
