"use client";

import {
  ArrowRight,
  BadgeDollarSign,
  FileCheck2,
  LoaderCircle,
  ReceiptText,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  formatGenAmount,
  trackCommitTransaction,
  type ConnectedCommitWallet,
  type TransactionProgress,
} from "@/lib/genlayer-browser";
import {
  quoteClaimMission,
  submitClaimMission,
  verifyFinalizedClaim,
  type ClaimMissionQuote,
  type FinalizedClaimProof,
} from "@/lib/genlayer-claim";
import {
  observeExternalDelivery,
  persistClaimTransaction,
  readPersistedClaimTransaction,
  unverifiedExternalDelivery,
  type ExternalDeliveryObservation,
  type PersistedClaimTransaction,
} from "@/lib/genlayer-delivery";

type ClaimMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

export function ClaimMissionFlow({
  wallet,
  initialMissionId = "",
}: ClaimMissionFlowProps) {
  const [
    missionId,
    setMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    quote,
    setQuote,
  ] = useState<ClaimMissionQuote | null>(
    null,
  );
  const [
    progress,
    setProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    proof,
    setProof,
  ] = useState<FinalizedClaimProof | null>(
    null,
  );
  const [
    busy,
    setBusy,
  ] = useState(false);
  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );
  const [
    claimRecord,
    setClaimRecord,
  ] = useState<PersistedClaimTransaction | null>(() =>
    readPersistedClaimTransaction(
      initialMissionId,
      wallet.address,
    ),
  );
  const [
    delivery,
    setDelivery,
  ] = useState<ExternalDeliveryObservation | null>(
    null,
  );
  const [
    deliveryBusy,
    setDeliveryBusy,
  ] = useState(false);

  function resetReview() {
    setQuote(null);
    setProgress(null);
    setProof(null);
    setDelivery(null);
    setError(null);
  }

  async function reviewClaim() {
    setBusy(true);
    setError(null);

    try {
      const next =
        await quoteClaimMission(
          wallet,
          missionId,
        );

      setQuote(next);
    } catch (caught: unknown) {
      setQuote(null);
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to preflight beneficiary claim.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function signClaim() {
    if (
      quote === null
      || busy
    ) {
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const txId =
        await submitClaimMission(
          wallet,
          quote,
        );

      setProgress({
        phase: "submitted",
        txId,
      });
      setClaimRecord({
        transactionId: txId,
        amount: quote.snapshot.missionClaimable,
      });
      persistClaimTransaction(
        quote.snapshot.mission.missionId,
        quote.snapshot.beneficiary,
        txId,
        quote.snapshot.missionClaimable,
      );

      const result =
        await trackCommitTransaction(
          txId,
          setProgress,
        );

      if (result.successful) {
        const observed =
          await observeExternalDelivery(
            wallet.client,
            txId,
            {
              recipient: quote.snapshot.beneficiary,
              amount: quote.snapshot.missionClaimable,
            },
          );

        setDelivery(observed);

        const finalized =
          await verifyFinalizedClaim(
            wallet,
            quote,
          );

        setProof(finalized);
      } else {
        setDelivery(
          unverifiedExternalDelivery(
            txId,
            "The parent claim did not finalize successfully. No external delivery is claimed.",
          ),
        );
      }
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Beneficiary claim failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function refreshDelivery() {
    if (
      claimRecord === null
      || deliveryBusy
    ) {
      return;
    }

    setDeliveryBusy(true);

    try {
      setDelivery(
        await observeExternalDelivery(
          wallet.client,
          claimRecord.transactionId,
          {
            recipient: wallet.address,
            amount: claimRecord.amount,
          },
        ),
      );
    } catch (caught: unknown) {
      setDelivery(
        unverifiedExternalDelivery(
          claimRecord.transactionId,
          caught instanceof Error
            ? caught.message
            : "The delivery observation could not be completed. No delivery outcome is claimed.",
        ),
      );
    } finally {
      setDeliveryBusy(false);
    }
  }

  function deliveryLabel(
    phase: ExternalDeliveryObservation["phase"],
  ): string {
    return phase === "DELIVERED"
      ? "DELIVERED"
      : phase === "FAILED"
        ? "FAILED — NO AUTOMATIC RETRY"
        : phase === "PENDING"
          ? "PENDING"
          : "UNVERIFIED";
  }

  return (
    <section className="claim-flow">
      <div className="claim-flow-heading">
        <div>
          <p>CLAIM / WITHDRAW</p>
          <h2>
            Pull the exact terminal entitlement and verify its finalized withdrawal record.
          </h2>
        </div>
        <span>
          BENEFICIARY / PULL PAYMENT
        </span>
      </div>

      <div className="claim-panel">
        <label className="claim-mission-input">
          <span>Mission ID</span>
          <input
            value={missionId}
            onChange={(event) => {
              const nextMissionId = event.target.value;
              setMissionId(
                nextMissionId,
              );
              setClaimRecord(
                readPersistedClaimTransaction(
                  nextMissionId,
                  wallet.address,
                ),
              );
              resetReview();
            }}
            placeholder="Mission ID"
            maxLength={512}
          />
        </label>

        <div className="claim-rule-grid">
          <div>
            <ShieldCheck
              size={17}
              aria-hidden="true"
            />
            <strong>Terminal allocation</strong>
            <span>
              Claims are available only after COMMITTED or ABORTED allocation
              is visible in finalized coordinator state.
            </span>
          </div>
          <div>
            <BadgeDollarSign
              size={17}
              aria-hidden="true"
            />
            <strong>Beneficiary pull payment</strong>
            <span>
              The connected wallet claims only its mission-specific
              entitlement. The contract zeros the entitlement before
              dispatching the native transfer.
            </span>
          </div>
          <div>
            <ReceiptText
              size={17}
              aria-hidden="true"
            />
            <strong>Receipt cross-check</strong>
            <span>
              Finalized claim verification requires the mission entitlement to
              be zero and an exact matching DISPATCHED withdrawal record by
              both index and direct ID.
            </span>
          </div>
        </div>

        {quote === null ? (
          <button
            className="mission-primary-button"
            type="button"
            disabled={
              busy
              || missionId.length === 0
            }
            onClick={reviewClaim}
          >
            {busy ? (
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
            Preflight beneficiary claim
          </button>
        ) : (
          <div className="claim-review">
            <dl>
              <div>
                <dt>Mission state</dt>
                <dd>
                  {quote.snapshot.mission.state}
                </dd>
              </div>
              <div>
                <dt>Decision</dt>
                <dd>
                  {quote.snapshot.mission.decision}
                </dd>
              </div>
              <div>
                <dt>Allocation applied</dt>
                <dd>
                  {quote.snapshot.mission.allocationApplied
                    ? "YES"
                    : "NO"}
                </dd>
              </div>
              <div>
                <dt>Beneficiary</dt>
                <dd>
                  {quote.snapshot.beneficiary}
                </dd>
              </div>
              <div>
                <dt>Mission claimable</dt>
                <dd>
                  {formatGenAmount(
                    quote.snapshot.missionClaimable,
                  )} GEN
                </dd>
              </div>
              <div>
                <dt>Aggregate claimable</dt>
                <dd>
                  {formatGenAmount(
                    quote.snapshot.aggregateClaimable,
                  )} GEN
                </dd>
              </div>
              <div>
                <dt>Withdrawal count before</dt>
                <dd>
                  {quote.snapshot.withdrawalCount}
                </dd>
              </div>
              <div>
                <dt>External recovery mode</dt>
                <dd>
                  {quote.snapshot.receipt.externalWithdrawalRecovery
                    ? "ENABLED"
                    : "DISABLED"}
                </dd>
              </div>
              <div>
                <dt>Quoted fee</dt>
                <dd>
                  {formatGenAmount(
                    quote.feeValue,
                  )} GEN
                </dd>
              </div>
            </dl>

            <div className="claim-final-warning">
              This is a nonpayable claim call. No mission value is sent into
              the coordinator. The wallet signs only the claim transaction and
              its quoted GenLayer fee deposit.
            </div>

            <button
              className="mission-primary-button"
              type="button"
              disabled={
                busy
                || progress !== null
              }
              onClick={signClaim}
            >
              {busy ? (
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
              Sign &amp; claim entitlement
            </button>
          </div>
        )}

        {progress !== null ? (
          <div className="claim-progress">
            <span>{progress.phase}</span>
            <code>{progress.txId}</code>
          </div>
        ) : null}

        {proof !== null ? (
          <div className="claim-proof">
            <div className="claim-proof-title">
              <FileCheck2
                size={18}
                aria-hidden="true"
              />
              <strong>
                Finalized withdrawal record verified
              </strong>
            </div>
            <dl>
              <div>
                <dt>Withdrawal ID</dt>
                <dd>{proof.withdrawal.withdrawalId}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{proof.withdrawal.status}</dd>
              </div>
              <div>
                <dt>Beneficiary</dt>
                <dd>{proof.withdrawal.beneficiary}</dd>
              </div>
              <div>
                <dt>Amount</dt>
                <dd>
                  {formatGenAmount(
                    proof.withdrawal.amount,
                  )} GEN
                </dd>
              </div>
              <div>
                <dt>Mission claimable after</dt>
                <dd>
                  {formatGenAmount(
                    proof.missionClaimableAfter,
                  )} GEN
                </dd>
              </div>
              <div>
                <dt>Withdrawal count after</dt>
                <dd>{proof.withdrawalCountAfter}</dd>
              </div>
            </dl>
            <p>
              DISPATCHED is the coordinator&apos;s withdrawal record. COMMIT
              does not present it as an external withdrawal-recovery mechanism;
              the frozen mission receipt declares
              external_withdrawal_recovery=false.
            </p>
          </div>
        ) : null}

        {claimRecord !== null ? (
          <div className="claim-delivery">
            <div className="claim-delivery-heading">
              <div>
                <span>EXTERNAL MESSAGE OBSERVATION</span>
                <strong>
                  {delivery === null
                    ? "Not checked"
                    : deliveryLabel(delivery.phase)}
                </strong>
              </div>
              <button
                className="mission-secondary-button claim-delivery-refresh"
                type="button"
                disabled={deliveryBusy}
                onClick={refreshDelivery}
              >
                {deliveryBusy ? (
                  <LoaderCircle
                    className="spin"
                    size={15}
                    aria-hidden="true"
                  />
                ) : null}
                Observe child transaction
              </button>
            </div>
            <p>
              The parent claim transaction is recorded locally so this status
              can be re-read after navigation. This is an operator observation
              from GenLayer&apos;s triggered-transaction API, not an onchain
              delivery receipt. A timeout or missing child ID is never treated
              as failure, and this app never retries automatically.
            </p>
            <dl>
              <div>
                <dt>Parent claim</dt>
                <dd>{claimRecord.transactionId}</dd>
              </div>
              <div>
                <dt>Triggered child</dt>
                <dd>
                  {delivery?.child?.transactionId
                    ?? "Not exposed"}
                </dd>
              </div>
              <div>
                <dt>Child lifecycle</dt>
                <dd>
                  {delivery?.child?.statusName
                    ?? "Unknown"}
                </dd>
              </div>
              <div>
                <dt>Execution result</dt>
                <dd>
                  {delivery?.child?.executionResultName
                    ?? "Unknown"}
                </dd>
              </div>
            </dl>
            {delivery !== null ? (
              <small>{delivery.reason}</small>
            ) : (
              <small>
                Select “Observe child transaction” to read the exact child
                transaction. No delivery outcome is assumed before then.
              </small>
            )}
          </div>
        ) : null}

        {error !== null ? (
          <p
            className="mission-error"
            role="alert"
          >
            {error}
          </p>
        ) : null}
      </div>
    </section>
  );
}
