import { useEffect, useState } from "react";
import { get } from "../api/client";

export interface ApiState<T> { data: T | null; loading: boolean; error: string | null }

export function useApi<T = any>(path: string, params: Record<string, string | number | undefined>): ApiState<T> {
  const [s, setS] = useState<ApiState<T>>({ data: null, loading: true, error: null });
  const key = path + JSON.stringify(params);
  useEffect(() => {
    let live = true;
    setS((p) => ({ ...p, loading: true, error: null }));
    get<T>(path, params).then((d) => live && setS({ data: d, loading: false, error: null }),
      (e) => live && setS({ data: null, loading: false, error: String(e.message ?? e) }));
    return () => { live = false; };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return s;
}
