import type { ReactNode } from "react";

interface StateBoundaryProps {
  loading: boolean;
  error: string | null;
  found?: boolean;
  emptyLabel: string;
  children: ReactNode;
}

export function StateBoundary({
  loading,
  error,
  found = true,
  emptyLabel,
  children,
}: StateBoundaryProps) {
  if (loading) {
    return (
      <div className="state-boundary state-loading" role="status">
        <span className="state-pulse" aria-hidden="true" />
        <div>
          <strong>Loading certified read state</strong>
          <p>Waiting for the read-only protocol API.</p>
        </div>
      </div>
    );
  }

  if (error !== null) {
    return (
      <div className="state-boundary state-error" role="alert">
        <strong>Read surface unavailable</strong>
        <p>{error}</p>
      </div>
    );
  }

  if (!found) {
    return (
      <div className="state-boundary state-empty">
        <strong>Not found</strong>
        <p>{emptyLabel}</p>
      </div>
    );
  }

  return <>{children}</>;
}
