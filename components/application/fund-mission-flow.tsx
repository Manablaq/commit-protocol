"use client";

import {
  ArrowRight,
  Check,
  LoaderCircle,
  RefreshCw,
  WalletCards,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  formatGenAmount,
  quoteFundMission,
  readMissionFundingSnapshot,
  submitFundMission,
  trackCommitTransaction,
  type ConnectedCommitWallet,
  type FundMissionQuote,
  type MissionFundingSnapshot,
  type TransactionProgress,
} from "@/lib/genlayer-browser";

type FundMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

function displayDeadline(
  timestamp: number,
): string {
  return new Date(
    timestamp * 1000,
  ).toLocaleString();
}

function remainingBudget(
  mission: MissionFundingSnapshot,
): bigint {
  const remaining =
    mission.budget
    - mission.fundedValue;

  return remaining > BigInt(0)
    ? remaining
    : BigInt(0);
}

export function FundMissionFlow({
  wallet,
  initialMissionId = "",
}: FundMissionFlowProps) {
  const [
    missionId,
    setMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    amountGen,
    setAmountGen,
  ] = useState("");
  const [
    quote,
    setQuote,
  ] = useState<FundMissionQuote | null>(
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
    verifiedMission,
    setVerifiedMission,
  ] = useState<MissionFundingSnapshot | null>(
    null,
  );
  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  function resetReview() {
    setQuote(
      null,
    );
    setProgress(
      null,
    );
    setVerifiedMission(
      null,
    );
    setError(
      null,
    );
  }

  async function reviewFunding() {
    setQuoteLoading(
      true,
    );
    setError(
      null,
    );
    setVerifiedMission(
      null,
    );

    try {
      const nextQuote =
        await quoteFundMission(
          wallet,
          missionId,
          amountGen,
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
          : "Unable to preflight mission funding.",
      );
    } finally {
      setQuoteLoading(
        false,
      );
    }
  }

  async function signAndFund() {
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
        await submitFundMission(
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

      const result =
        await trackCommitTransaction(
          txId,
          setProgress,
        );

      if (result.successful) {
        const refreshed =
          await readMissionFundingSnapshot(
            wallet,
            missionId,
          );

        setVerifiedMission(
          refreshed,
        );
      }
    } catch (nextError: unknown) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Mission funding failed.",
      );
    } finally {
      setSubmitLoading(
        false,
      );
    }
  }

  const finalized =
    progress?.phase === "finalized";

  return (
    <section className="fund-flow">
      <div className="fund-flow-heading">
        <div>
          <p>FUND / MISSION</p>
          <h2>
            Deposit only after the mission passes principal and budget checks.
          </h2>
        </div>
        <span>
          PAYABLE · PRINCIPAL ONLY
        </span>
      </div>

      <div className="fund-flow-grid">
        <div className="fund-entry">
          <label>
            <span>Mission ID</span>
            <input
              value={missionId}
              onChange={(event) => {
                setMissionId(
                  event.target.value,
                );
                resetReview();
              }}
              placeholder="Mission created by this wallet"
              maxLength={512}
            />
          </label>

          <label>
            <span>Funding amount · GEN</span>
            <input
              value={amountGen}
              onChange={(event) => {
                setAmountGen(
                  event.target.value,
                );
                resetReview();
              }}
              placeholder="0.5"
              inputMode="decimal"
            />
          </label>

          <div className="fund-warning">
            COMMIT reads the mission before signing. A different principal,
            non-PREPARING mission, expired preparation window, or amount above
            the remaining budget is rejected in the browser before the wallet
            is asked to approve a transaction.
          </div>

          {quote === null ? (
            <button
              className="mission-primary-button"
              type="button"
              onClick={reviewFunding}
              disabled={
                quoteLoading
                || missionId.length === 0
                || amountGen.length === 0
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
              Preflight &amp; review funding
            </button>
          ) : (
            <>
              <button
                className="mission-primary-button"
                type="button"
                onClick={signAndFund}
                disabled={
                  submitLoading
                  || progress !== null
                }
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
                Sign &amp; fund mission
              </button>
              {progress === null ? (
                <button
                  className="mission-secondary-button"
                  type="button"
                  onClick={() => setQuote(null)}
                >
                  Edit funding
                </button>
              ) : null}
            </>
          )}

          {error !== null ? (
            <p className="mission-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <aside className="fund-review">
          {quote === null ? (
            <div className="fund-empty">
              <RefreshCw
                size={23}
                aria-hidden="true"
              />
              <strong>
                Waiting for mission preflight
              </strong>
              <p>
                No value is signed or submitted while this panel is empty.
              </p>
            </div>
          ) : (
            <>
              <div className="fund-review-status">
                <Check
                  size={20}
                  aria-hidden="true"
                />
                <div>
                  <span>Preflight passed</span>
                  <strong>
                    {quote.mission.state}
                  </strong>
                </div>
              </div>

              <dl className="fund-review-list">
                <div>
                  <dt>Principal</dt>
                  <dd>{quote.mission.principal}</dd>
                </div>
                <div>
                  <dt>Budget</dt>
                  <dd>
                    {formatGenAmount(
                      quote.mission.budget,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Already funded</dt>
                  <dd>
                    {formatGenAmount(
                      quote.mission.fundedValue,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Remaining before funding</dt>
                  <dd>
                    {formatGenAmount(
                      remainingBudget(
                        quote.mission,
                      ),
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Funding value</dt>
                  <dd>
                    {formatGenAmount(
                      quote.amount,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Quoted fee deposit</dt>
                  <dd>
                    {formatGenAmount(
                      quote.feeValue,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Wallet balance</dt>
                  <dd>
                    {quote.preflight.balanceGen} GEN
                  </dd>
                </div>
                <div>
                  <dt>Preparation deadline</dt>
                  <dd>
                    {displayDeadline(
                      quote.mission.prepareDeadline,
                    )}
                  </dd>
                </div>
              </dl>
            </>
          )}
        </aside>
      </div>

      {progress !== null ? (
        <div className="fund-progress">
          <div>
            <span>
              {progress.phase === "submitted"
                ? "Submitted"
                : progress.phase === "accepted"
                  ? "Accepted / provisional"
                  : progress.successful
                    ? "Finalized / funded"
                    : "Finalized / execution failed"}
            </span>
            <code>{progress.txId}</code>
          </div>

          {progress.phase !== "submitted" ? (
            <div>
              <span>{progress.statusName}</span>
              <span>
                {progress.executionResultName}
              </span>
            </div>
          ) : null}

          {finalized && verifiedMission !== null ? (
            <strong>
              Verified funded value ·{" "}
              {formatGenAmount(
                verifiedMission.fundedValue,
              )} GEN
            </strong>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
