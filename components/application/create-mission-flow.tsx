"use client";

import {
  ArrowRight,
  Check,
  LoaderCircle,
  RotateCcw,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import {
  COMMIT_POLICY_DIGEST,
  formatGenAmount,
  quoteCreateMission,
  submitCreateMission,
  trackCommitTransaction,
  validateMissionDraft,
  type ConnectedCommitWallet,
  type CreateMissionQuote,
  type MissionDraft,
  type TransactionProgress,
} from "@/lib/genlayer-browser";

type CreateMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  onMissionFinalized?: (
    missionId: string,
  ) => void;
};

function defaultDeadline(
  hoursFromNow: number,
): string {
  const date = new Date(
    Date.now()
    + hoursFromNow * 60 * 60 * 1000,
  );

  const local = new Date(
    date.getTime()
    - date.getTimezoneOffset() * 60_000,
  );

  return local
    .toISOString()
    .slice(0, 16);
}

function unixTimestamp(
  value: string,
): number {
  const milliseconds = new Date(
    value,
  ).getTime();

  if (!Number.isFinite(milliseconds)) {
    return 0;
  }

  return Math.floor(
    milliseconds / 1000,
  );
}

function shorten(
  value: string,
): string {
  if (value.length < 18) {
    return value;
  }

  return `${value.slice(0, 10)}…${value.slice(-8)}`;
}

export function CreateMissionFlow({
  wallet,
  onMissionFinalized,
}: CreateMissionFlowProps) {
  const [
    missionId,
    setMissionId,
  ] = useState("");
  const [
    objective,
    setObjective,
  ] = useState("");
  const [
    budgetGen,
    setBudgetGen,
  ] = useState("");
  const [
    refundBeneficiary,
    setRefundBeneficiary,
  ] = useState<string>(
    wallet.address,
  );
  const [
    prepareAt,
    setPrepareAt,
  ] = useState(
    () => defaultDeadline(24),
  );
  const [
    recoveryAt,
    setRecoveryAt,
  ] = useState(
    () => defaultDeadline(168),
  );

  const [
    quote,
    setQuote,
  ] = useState<CreateMissionQuote | null>(
    null,
  );
  const [
    quoteLoading,
    setQuoteLoading,
  ] = useState(false);
  const [
    submitLoading,
    setSubmitLoading,
  ] = useState(false);
  const [
    progress,
    setProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const draft = useMemo<MissionDraft>(
    () => ({
      missionId,
      objective,
      budgetGen,
      refundBeneficiary,
      prepareDeadline:
        unixTimestamp(
          prepareAt,
        ),
      recoveryDeadline:
        unixTimestamp(
          recoveryAt,
        ),
    }),
    [
      missionId,
      objective,
      budgetGen,
      refundBeneficiary,
      prepareAt,
      recoveryAt,
    ],
  );

  const validationErrors =
    useMemo(
      () => validateMissionDraft(
        draft,
      ),
      [draft],
    );

  const finalized =
    progress?.phase === "finalized";

  const finalSuccess =
    finalized
    && progress.successful;

  function resetFlow() {
    setQuote(
      null,
    );
    setProgress(
      null,
    );
    setError(
      null,
    );
  }

  async function createQuote() {
    setError(
      null,
    );

    if (
      validationErrors.length > 0
    ) {
      setError(
        validationErrors.join(" "),
      );
      return;
    }

    setQuoteLoading(
      true,
    );

    try {
      const nextQuote =
        await quoteCreateMission(
          wallet,
          draft,
        );

      setQuote(
        nextQuote,
      );
    } catch (nextError: unknown) {
      setQuote(
        null,
      );
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Unable to quote this mission.",
      );
    } finally {
      setQuoteLoading(
        false,
      );
    }
  }

  async function signAndSubmit() {
    if (
      quote === null
      || submitLoading
    ) {
      return;
    }

    setSubmitLoading(
      true,
    );
    setError(
      null,
    );

    try {
      const txId =
        await submitCreateMission(
          wallet,
          quote,
        );

      localStorage.setItem(
        "commit:last-transaction",
        txId,
      );

      setProgress({
        phase: "submitted",
        txId,
      });

      const finalResult =
        await trackCommitTransaction(
          txId,
          setProgress,
        );

      if (finalResult.successful) {
        localStorage.setItem(
          "commit:last-mission",
          missionId,
        );
        onMissionFinalized?.(
          missionId,
        );
      }
    } catch (nextError: unknown) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Mission submission failed.",
      );
    } finally {
      setSubmitLoading(
        false,
      );
    }
  }

  return (
    <section className="mission-flow">
      <div className="mission-flow-heading">
        <div>
          <p>CREATE / MISSION</p>
          <h2>Turn intent into a protocol-bound commitment.</h2>
        </div>
        <span className="mission-step">
          {quote === null
            ? "01 · Define"
            : progress === null
              ? "02 · Review"
              : "03 · Track"}
        </span>
      </div>

      {progress === null ? (
        <div className="mission-flow-grid">
          <div className="mission-form">
            <label>
              <span>Mission ID</span>
              <input
                value={missionId}
                onChange={(event) => {
                  setMissionId(
                    event.target.value,
                  );
                  resetFlow();
                }}
                placeholder="e.g. supplier-verification-001"
                maxLength={512}
              />
            </label>

            <label className="mission-field-wide">
              <span>Objective</span>
              <textarea
                value={objective}
                onChange={(event) => {
                  setObjective(
                    event.target.value,
                  );
                  resetFlow();
                }}
                placeholder="State the exact mission objective."
                maxLength={512}
                rows={5}
              />
            </label>

            <label>
              <span>Budget · GEN</span>
              <input
                value={budgetGen}
                onChange={(event) => {
                  setBudgetGen(
                    event.target.value,
                  );
                  resetFlow();
                }}
                placeholder="1.0"
                inputMode="decimal"
              />
            </label>

            <label>
              <span>Refund beneficiary</span>
              <input
                value={refundBeneficiary}
                onChange={(event) => {
                  setRefundBeneficiary(
                    event.target.value,
                  );
                  resetFlow();
                }}
                spellCheck={false}
              />
            </label>

            <label>
              <span>Preparation deadline</span>
              <input
                type="datetime-local"
                value={prepareAt}
                onChange={(event) => {
                  setPrepareAt(
                    event.target.value,
                  );
                  resetFlow();
                }}
              />
            </label>

            <label>
              <span>Recovery deadline</span>
              <input
                type="datetime-local"
                value={recoveryAt}
                onChange={(event) => {
                  setRecoveryAt(
                    event.target.value,
                  );
                  resetFlow();
                }}
              />
            </label>
          </div>

          <aside className="mission-review">
            <div className="mission-review-top">
              <ShieldCheck
                size={21}
                aria-hidden="true"
              />
              <div>
                <span>Contract policy</span>
                <strong>Locked by deployed coordinator</strong>
              </div>
            </div>

            <dl className="mission-review-list">
              <div>
                <dt>Principal</dt>
                <dd>{shorten(wallet.address)}</dd>
              </div>
              <div>
                <dt>Policy digest</dt>
                <dd>{shorten(COMMIT_POLICY_DIGEST)}</dd>
              </div>
              <div>
                <dt>Budget</dt>
                <dd>{budgetGen || "—"} GEN</dd>
              </div>
              <div>
                <dt>Preparation</dt>
                <dd>{prepareAt || "—"}</dd>
              </div>
              <div>
                <dt>Recovery</dt>
                <dd>{recoveryAt || "—"}</dd>
              </div>
            </dl>

            {quote === null ? (
              <button
                className="mission-primary-button"
                type="button"
                onClick={createQuote}
                disabled={
                  quoteLoading
                  || validationErrors.length > 0
                }
              >
                {quoteLoading ? (
                  <LoaderCircle
                    className="spin"
                    size={17}
                    aria-hidden="true"
                  />
                ) : (
                  <ArrowRight
                    size={17}
                    aria-hidden="true"
                  />
                )}
                Review fees
              </button>
            ) : (
              <div className="mission-quote">
                <div>
                  <span>Maximum fee deposit</span>
                  <strong>
                    {formatGenAmount(
                      quote.feeValue,
                    )} GEN
                  </strong>
                </div>
                <p>
                  Your mission budget is not transferred by
                  <code> create_mission</code>. Funding is a separate
                  payable protocol action.
                </p>
                <button
                  className="mission-primary-button"
                  type="button"
                  onClick={signAndSubmit}
                  disabled={submitLoading}
                >
                  {submitLoading ? (
                    <LoaderCircle
                      className="spin"
                      size={17}
                      aria-hidden="true"
                    />
                  ) : (
                    <WalletCards
                      size={17}
                      aria-hidden="true"
                    />
                  )}
                  Sign &amp; create mission
                </button>
                <button
                  className="mission-secondary-button"
                  type="button"
                  onClick={() => setQuote(null)}
                  disabled={submitLoading}
                >
                  Edit mission
                </button>
              </div>
            )}

            {error !== null ? (
              <p className="mission-error" role="alert">
                {error}
              </p>
            ) : null}
          </aside>
        </div>
      ) : (
        <div className="mission-progress">
          <div className="mission-progress-icon">
            {finalized ? (
              <Check
                size={28}
                aria-hidden="true"
              />
            ) : (
              <LoaderCircle
                className="spin"
                size={28}
                aria-hidden="true"
              />
            )}
          </div>

          <div className="mission-progress-copy">
            <p>
              {progress.phase === "submitted"
                ? "Transaction submitted"
                : progress.phase === "accepted"
                  ? "Consensus accepted"
                  : finalSuccess
                    ? "Mission finalized"
                    : "Transaction finalized with execution failure"}
            </p>
            <h3>
              {finalSuccess
                ? "Your mission now exists on COMMIT."
                : "Tracking the exact GenLayer transaction lifecycle."}
            </h3>
            <code>{progress.txId}</code>

            {progress.phase !== "submitted" ? (
              <div className="mission-progress-meta">
                <span>
                  Status · {progress.statusName}
                </span>
                <span>
                  Execution · {progress.executionResultName}
                </span>
              </div>
            ) : null}
          </div>

          <div className="mission-progress-actions">
            <a
              className="mission-secondary-button"
              href="/verify"
            >
              Open verification center
            </a>
            {finalized ? (
              <button
                className="mission-primary-button"
                type="button"
                onClick={() => {
                  setMissionId("");
                  setObjective("");
                  setBudgetGen("");
                  setQuote(null);
                  setProgress(null);
                  setError(null);
                }}
              >
                <RotateCcw
                  size={16}
                  aria-hidden="true"
                />
                Create another
              </button>
            ) : null}
          </div>

          {error !== null ? (
            <p className="mission-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
