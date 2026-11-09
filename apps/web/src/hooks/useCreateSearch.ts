import { useCallback, useState } from "react";
import { ApiError, api } from "../api/client";
import type { Created, SearchRequest } from "../api/types";

export function useCreateSearch() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  const createSearch = useCallback(async (body: SearchRequest): Promise<Created | null> => {
    setSubmitting(true);
    setError(null);
    try {
      return await api.createSearch(body);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return null;
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { createSearch, submitting, error };
}
