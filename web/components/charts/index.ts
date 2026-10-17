import dynamic from "next/dynamic";
import { createElement } from "react";
import { Skeleton } from "@/components/ui/misc";

export type { BarSeries } from "./bars";
export const Bars = dynamic(() => import("./bars"), { ssr: false, loading: () => createElement(Skeleton, { className: "h-full" }) });
