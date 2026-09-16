"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Gavel,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import {
  appealChargeLabel,
  appealPhaseLabel,
  type AppealLifecycleSnapshot,
} from "@/lib/genlayer-appeal";

type AppealPanelProps = {
  snapshot: AppealLifecycleSnapshot | null;
  loading: boolean;
  busy?: boolean;
  error?: string | null;
  submittedTxId?: string | null;
  readOnly?: boolean;
  onRefresh?: () => void;
  onAppeal?: () => void;
};

export function AppealPanel({
  snapshot,
  loading,
  busy = false,
  error = null,
  submittedTxId = null,
  readOnly = false,
  onRefresh,
  onAppeal,
}: AppealPanelProps) {
  const finalSuccess = snapshot?.phase === "FINALIZED";
  const finalFailure = snapshot?.phase === "FINALIZED_ERROR";
  const finalUnknown = snapshot?.phase === "FINALIZED_UNKNOWN";

  const title = snapshot === null
    ? "Add the evaluation transaction"
    : appealPhaseLabel(snapshot.phase);

  return (
    <article className="justice-panel appeal-panel">
      <div className="justice-panel-heading">
        <div>
          <p className="card-kicker">Native GenLayer appeal</p>
          <h3>{title}</h3>
        </div>
        {finalSuccess ? (
          <CheckCircle2 className="justice-success-icon" size={20} aria-hidden="true" />
        ) : finalFailure || finalUnknown ? (
          <AlertTriangle size={20} aria-hidden="true" />
        ) : (
          <Gavel size={20} aria-hidden="true" />
        )}
      </div>

      {loading ? (
        <div className="justice-inline-status" role="status">
          <LoaderCircle className="spin" size={16} aria-hidden="true" />
          Reading the authoritative GenLayer lifecycle…
        </div>
      ) : snapshot === null ? (
        <div className="justice-empty-copy">
          <p>
            The contract does not store the evaluation transaction ID as an
            application field. Paste the exact GenLayer evaluation transaction
            to read its appeal window and finality directly from the network.
          </p>
        </div>
      ) : (
        <>
          <div className={`justice-verdict-banner ${finalSuccess ? "is-final" : finalFailure || finalUnknown ? "is-error" : "is-provisional"}`}>
            <ShieldCheck size={18} aria-hidden="true" />
            <div>
              <strong>
                {finalSuccess
                  ? "Final verdict"
                  : finalFailure
                    ? "Finalized execution failed"
                    : finalUnknown
                      ? "Finalized result unavailable"
                      : snapshot.decisionActive
                        ? "Provisional verdict"
                        : "Evaluation is still processing"}
              </strong>
              <span>
                {finalSuccess
                  ? "The evaluation transaction is finalized; the appeal window is closed."
                  : finalFailure
                    ? "The protocol finalized this transaction, but its execution result was not successful. No durable verdict is claimed."
                    : finalUnknown
                      ? "The protocol finalized this transaction, but the execution result is unavailable. No durable verdict is claimed."
                      : snapshot.canAppeal
                        ? "Anyone may challenge this decision before finality."
                        : "No appeal action is currently available from the authoritative lifecycle."}
              </span>
            </div>
          </div>

          <dl className="justice-fact-grid">
            <div>
              <dt>Stored status</dt>
              <dd>{snapshot.storedStatus}</dd>
            </div>
            <div>
              <dt>Projected status</dt>
              <dd>{snapshot.projectedStatus}</dd>
            </div>
            <div>
              <dt>Resolution action</dt>
              <dd>{snapshot.resolutionAction}</dd>
            </div>
            <div>
              <dt>Decision identity</dt>
              <dd>{snapshot.decisionId ?? "Not active"}</dd>
            </div>
            <div>
              <dt>Appeal charge</dt>
              <dd>{appealChargeLabel(snapshot.appealCharge)}</dd>
            </div>
            <div>
              <dt>Appeal availability</dt>
              <dd>{snapshot.canAppeal ? "Available" : "Unavailable"}</dd>
            </div>
            <div>
              <dt>Transaction target</dt>
              <dd>{snapshot.transactionTarget}</dd>
            </div>
            <div>
              <dt>Transaction method</dt>
              <dd>{snapshot.transactionFunctionName}</dd>
            </div>
            <div>
              <dt>Mission argument</dt>
              <dd>{snapshot.transactionMissionId}</dd>
            </div>
            <div>
              <dt>Execution result</dt>
              <dd>{snapshot.executionResultName ?? "Unavailable"}</dd>
            </div>
          </dl>

          {snapshot.phase === "APPEAL_IN_PROGRESS" ? (
            <div className="justice-inline-status">
              <LoaderCircle className="spin" size={16} aria-hidden="true" />
              Fresh validators are rechecking the active decision. The same
              transaction ID remains the source of truth.
            </div>
          ) : null}

          {snapshot.phase === "FINALIZED" ? (
            <div className="justice-inline-status is-success">
              <CheckCircle2 size={16} aria-hidden="true" />
              Finality is proven by the stored GenLayer lifecycle, not by a
              frontend timer.
            </div>
          ) : null}

          {finalFailure || finalUnknown ? (
            <div className="justice-inline-status is-error">
              <AlertTriangle size={16} aria-hidden="true" />
              This transaction is not presented as a successful durable
              verdict because finality and successful execution are separate
              facts.
            </div>
          ) : null}

          {snapshot.canAppeal && !readOnly ? (
            <button
              className="mission-primary-button justice-appeal-button"
              type="button"
              onClick={onAppeal}
              disabled={busy || loading}
            >
              {busy ? (
                <LoaderCircle className="spin" size={17} aria-hidden="true" />
              ) : (
                <Gavel size={17} aria-hidden="true" />
              )}
              {busy ? "Submitting appeal…" : "Appeal this verdict"}
            </button>
          ) : null}

          {readOnly && snapshot.canAppeal ? (
            <p className="justice-read-only-note">
              Read-only verification. Connect a wallet in the Case Room to
              submit the exact authoritative appeal charge.
            </p>
          ) : null}

          {submittedTxId !== null ? (
            <div className="justice-submission-note">
              <strong>Appeal submission accepted by the wallet</strong>
              <code>{submittedTxId}</code>
              <span>Refresh the lifecycle to observe the fresh validator stages.</span>
            </div>
          ) : null}
        </>
      )}

      {error !== null ? (
        <div className="justice-error" role="alert">
          <AlertTriangle size={16} aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}

      {onRefresh !== undefined ? (
        <button
          className="mission-secondary-button justice-refresh-button"
          type="button"
          onClick={onRefresh}
          disabled={loading || busy}
        >
          <RefreshCw size={16} aria-hidden="true" />
          Refresh lifecycle
        </button>
      ) : null}
    </article>
  );
}
