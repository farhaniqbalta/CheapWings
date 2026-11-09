import { useCallback, useState } from "react";
import { api } from "../api/client";

export function useCancelSearch() {
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const cancelSearch = useCallback(async (jobId: string) => {
    setCancelling(true);
    setError(null);
    try {
      await api.cancelSearch(jobId);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setCancelling(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  return { cancelSearch, cancelling, error, clearError };
}
