"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./api";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const run = useCallback(() => {
    setLoading(true); setError(null);
    fnRef.current().then((d) => { setData(d); setLoading(false); }).catch((e: unknown) => { setError(e instanceof ApiError && e.status === 0 ? "offline" : e instanceof Error ? e.message : "error"); setLoading(false); });
  }, []);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(run, deps);
  return { data, error, loading, reload: run };
}
