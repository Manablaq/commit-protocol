"use client";

import {
  ArrowRight,
  CircleAlert,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Scale,
  ShieldAlert,
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
  inspectResolutionState,
  quoteEvaluateMission,
  quoteExpireMission,
  quoteRepairEvidence,
  submitEvaluateMission,
  submitExpireMission,
  submitRepairEvidence,
  verifyFinalizedRecovery,
  verifyFinalizedRepair,
  type EvaluateMissionQuote,
  type EvidenceRepairSnapshot,
  type ExpireMissionQuote,
  type RepairEvidenceQuote,
  type ResolutionInspection,
} from "@/lib/genlayer-resolution";

type ResolutionMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

function positiveInteger(
  value: string,
): number {
  if (
    !/^[1-9][0-9]*$/.test(value)
  ) {
    return 0;
  }

  const parsed =
    Number(value);

  return Number.isSafeInteger(parsed)
    ? parsed
    : 0;
}

export function ResolutionMissionFlow({
  wallet,
  initialMissionId = "",
}: ResolutionMissionFlowProps) {
  const [
    missionId,
    setMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    inspection,
    setInspection,
  ] = useState<ResolutionInspection | null>(
    null,
  );
  const [
    inspectBusy,
    setInspectBusy,
  ] = useState(false);
  const [
    inspectError,
    setInspectError,
  ] = useState<string | null>(
    null,
  );

  const [
    evaluateQuote,
    setEvaluateQuote,
  ] = useState<EvaluateMissionQuote | null>(
    null,
  );
  const [
    evaluateProgress,
    setEvaluateProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    evaluateBusy,
    setEvaluateBusy,
  ] = useState(false);
  const [
    evaluateError,
    setEvaluateError,
  ] = useState<string | null>(
    null,
  );

  const [
    repairEvidenceId,
    setRepairEvidenceId,
  ] = useState("");
  const [
    repairRecordVersion,
    setRepairRecordVersion,
  ] = useState("");
  const [
    repairQuote,
    setRepairQuote,
  ] = useState<RepairEvidenceQuote | null>(
    null,
  );
  const [
    repairProgress,
    setRepairProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    verifiedRepair,
    setVerifiedRepair,
  ] = useState<EvidenceRepairSnapshot | null>(
    null,
  );
  const [
    repairBusy,
    setRepairBusy,
  ] = useState(false);
  const [
    repairError,
    setRepairError,
  ] = useState<string | null>(
    null,
  );

  const [
    expireQuote,
    setExpireQuote,
  ] = useState<ExpireMissionQuote | null>(
    null,
  );
  const [
    expireProgress,
    setExpireProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    expireBusy,
    setExpireBusy,
  ] = useState(false);
  const [
    expireError,
    setExpireError,
  ] = useState<string | null>(
    null,
  );

  function resetAll() {
    setInspection(null);
    setInspectError(null);
    setEvaluateQuote(null);
    setEvaluateProgress(null);
    setEvaluateError(null);
    setRepairQuote(null);
    setRepairProgress(null);
    setVerifiedRepair(null);
    setRepairError(null);
    setExpireQuote(null);
    setExpireProgress(null);
    setExpireError(null);
  }

  async function refreshFinalized() {
    setInspectBusy(true);
    setInspectError(null);

    try {
      const next =
        await inspectResolutionState(
          wallet,
          missionId,
        );

      setInspection(next);
    } catch (caught: unknown) {
      setInspection(null);
      setInspectError(
        caught instanceof Error
          ? caught.message
          : "Unable to read finalized resolution state.",
      );
    } finally {
      setInspectBusy(false);
    }
  }

  async function reviewEvaluation() {
    setEvaluateBusy(true);
    setEvaluateError(null);

    try {
      const next =
        await quoteEvaluateMission(
          wallet,
          missionId,
        );

      setEvaluateQuote(next);
    } catch (caught: unknown) {
      setEvaluateQuote(null);
      setEvaluateError(
        caught instanceof Error
          ? caught.message
          : "Unable to preflight evaluation.",
      );
    } finally {
      setEvaluateBusy(false);
    }
  }

  async function signEvaluation() {
    if (
      evaluateQuote === null
      || evaluateBusy
    ) {
      return;
    }

    setEvaluateBusy(true);
    setEvaluateError(null);

    try {
      const txId =
        await submitEvaluateMission(
          wallet,
          evaluateQuote,
        );

      localStorage.setItem(
        `commit:evaluation:${missionId}`,
        txId,
      );

      setEvaluateProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setEvaluateProgress,
        );

      if (result.successful) {
        const next =
          await inspectResolutionState(
            wallet,
            missionId,
          );

        setInspection(next);
      }
    } catch (caught: unknown) {
      setEvaluateError(
        caught instanceof Error
          ? caught.message
          : "Mission evaluation failed.",
      );
    } finally {
      setEvaluateBusy(false);
    }
  }

  async function reviewRepair() {
    setRepairBusy(true);
    setRepairError(null);

    try {
      const next =
        await quoteRepairEvidence(
          wallet,
          {
            missionId,
            evidenceId:
              repairEvidenceId,
            recordVersion:
              positiveInteger(
                repairRecordVersion,
              ),
          },
        );

      setRepairQuote(next);
    } catch (caught: unknown) {
      setRepairQuote(null);
      setRepairError(
        caught instanceof Error
          ? caught.message
          : "Unable to preflight evidence repair.",
      );
    } finally {
      setRepairBusy(false);
    }
  }

  async function signRepair() {
    if (
      repairQuote === null
      || repairBusy
    ) {
      return;
    }

    setRepairBusy(true);
    setRepairError(null);

    try {
      const txId =
        await submitRepairEvidence(
          wallet,
          repairQuote,
        );

      setRepairProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setRepairProgress,
        );

      if (result.successful) {
        const repair =
          await verifyFinalizedRepair(
            wallet,
            missionId,
            repairEvidenceId,
            positiveInteger(
              repairRecordVersion,
            ),
          );

        setVerifiedRepair(repair);
      }
    } catch (caught: unknown) {
      setRepairError(
        caught instanceof Error
          ? caught.message
          : "Evidence repair failed.",
      );
    } finally {
      setRepairBusy(false);
    }
  }

  async function reviewExpiry() {
    setExpireBusy(true);
    setExpireError(null);

    try {
      const next =
        await quoteExpireMission(
          wallet,
          missionId,
        );

      setExpireQuote(next);
    } catch (caught: unknown) {
      setExpireQuote(null);
      setExpireError(
        caught instanceof Error
          ? caught.message
          : "Unable to preflight deadline recovery.",
      );
    } finally {
      setExpireBusy(false);
    }
  }

  async function signExpiry() {
    if (
      expireQuote === null
      || expireBusy
    ) {
      return;
    }

    setExpireBusy(true);
    setExpireError(null);

    try {
      const txId =
        await submitExpireMission(
          wallet,
          expireQuote,
        );

      setExpireProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setExpireProgress,
        );

      if (result.successful) {
        const next =
          await verifyFinalizedRecovery(
            wallet,
            missionId,
          );

        setInspection(next);
      }
    } catch (caught: unknown) {
      setExpireError(
        caught instanceof Error
          ? caught.message
          : "Deadline recovery failed.",
      );
    } finally {
      setExpireBusy(false);
    }
  }

  return (
    <section className="resolution-flow">
      <div className="resolution-flow-heading">
        <div>
          <p>RESOLVE / MISSION</p>
          <h2>
            Evaluate evidence, repair failures, and prove allocation only from finalized state.
          </h2>
        </div>
        <span>
          PERMISSIONLESS EVALUATION + RECOVERY
        </span>
      </div>

      <div className="resolution-panel">
        <label className="resolution-mission-input">
          <span>Mission ID</span>
          <input
            value={missionId}
            onChange={(event) => {
              setMissionId(
                event.target.value,
              );
              resetAll();
            }}
            placeholder="Mission ID"
            maxLength={512}
          />
        </label>

        <button
          className="mission-secondary-button"
          type="button"
          disabled={
            inspectBusy
            || missionId.length === 0
          }
          onClick={refreshFinalized}
        >
          {inspectBusy ? (
            <LoaderCircle
              className="spin"
              size={17}
              aria-hidden="true"
            />
          ) : (
            <RefreshCw
              size={17}
              aria-hidden="true"
            />
          )}
          Refresh finalized resolution
        </button>

        {inspection !== null ? (
          <div className="resolution-status">
            <div>
              <span>Finalized classification</span>
              <strong>{inspection.classification}</strong>
            </div>
            <div>
              <span>Mission state</span>
              <strong>{inspection.mission.state}</strong>
            </div>
            <div>
              <span>Decision</span>
              <strong>
                {inspection.mission.decision || "—"}
              </strong>
            </div>
            <div>
              <span>Reason</span>
              <strong>
                {inspection.mission.reasonCode || "—"}
              </strong>
            </div>
            <div>
              <span>Allocation applied</span>
              <strong>
                {inspection.mission.allocationApplied
                  ? "YES"
                  : "NO"}
              </strong>
            </div>
            <div>
              <span>Refund entitlement</span>
              <strong>
                {formatGenAmount(
                  inspection.mission.refundEntitlement,
                )} GEN
              </strong>
            </div>
          </div>
        ) : null}

        {inspectError !== null ? (
          <p
            className="mission-error"
            role="alert"
          >
            {inspectError}
          </p>
        ) : null}

        <div className="resolution-rule-note">
          <Scale
            size={18}
            aria-hidden="true"
          />
          <p>
            Evaluation is permissionless after sealing. Validator nondeterminism
            fetches the bound evidence; the browser does not decide eligibility.
            A finalized evaluation transaction may leave the mission SEALED for
            repair, move it to DECISION_PENDING, or later resolve to
            COMMITTED/ABORTED after the contract&apos;s self-only finalized
            apply_decision message.
          </p>
        </div>

        <div className="resolution-action-grid">
          <article>
            <div className="resolution-card-title">
              <Scale
                size={18}
                aria-hidden="true"
              />
              <div>
                <p>01 / EVALUATE</p>
                <h3>Trigger validator evaluation.</h3>
              </div>
            </div>

            {evaluateQuote === null ? (
              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  evaluateBusy
                  || missionId.length === 0
                }
                onClick={reviewEvaluation}
              >
                {evaluateBusy ? (
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
                Preflight evaluation
              </button>
            ) : (
              <div className="resolution-review">
                <dl>
                  <div>
                    <dt>State</dt>
                    <dd>{evaluateQuote.mission.state}</dd>
                  </div>
                  <div>
                    <dt>Evaluation count</dt>
                    <dd>{evaluateQuote.mission.evaluationCount}</dd>
                  </div>
                  <div>
                    <dt>Recovery deadline</dt>
                    <dd>{evaluateQuote.mission.recoveryDeadline}</dd>
                  </div>
                  <div>
                    <dt>Quoted fee</dt>
                    <dd>
                      {formatGenAmount(
                        evaluateQuote.feeValue,
                      )} GEN
                    </dd>
                  </div>
                </dl>

                <button
                  className="mission-primary-button"
                  type="button"
                  disabled={
                    evaluateBusy
                    || evaluateProgress !== null
                  }
                  onClick={signEvaluation}
                >
                  <WalletCards
                    size={17}
                    aria-hidden="true"
                  />
                  Sign &amp; evaluate mission
                </button>
              </div>
            )}

            {evaluateProgress !== null ? (
              <div className="resolution-progress">
                <span>{evaluateProgress.phase}</span>
                <code>{evaluateProgress.txId}</code>
              </div>
            ) : null}

            {evaluateError !== null ? (
              <p
                className="mission-error"
                role="alert"
              >
                {evaluateError}
              </p>
            ) : null}
          </article>

          <article>
            <div className="resolution-card-title">
              <RotateCcw
                size={18}
                aria-hidden="true"
              />
              <div>
                <p>02 / REPAIR</p>
                <h3>Bind a newer attested record after a correctable failure.</h3>
              </div>
            </div>

            <label>
              <span>Evidence ID</span>
              <input
                value={repairEvidenceId}
                onChange={(event) => {
                  setRepairEvidenceId(
                    event.target.value,
                  );
                  setRepairQuote(null);
                  setRepairProgress(null);
                  setVerifiedRepair(null);
                }}
                placeholder="evidence-primary"
              />
            </label>

            <label>
              <span>New record version</span>
              <input
                value={repairRecordVersion}
                onChange={(event) => {
                  setRepairRecordVersion(
                    event.target.value,
                  );
                  setRepairQuote(null);
                  setRepairProgress(null);
                  setVerifiedRepair(null);
                }}
                inputMode="numeric"
                placeholder="2"
              />
            </label>

            {repairQuote === null ? (
              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  repairBusy
                  || missionId.length === 0
                  || repairEvidenceId.length === 0
                  || repairRecordVersion.length === 0
                }
                onClick={reviewRepair}
              >
                <ArrowRight
                  size={17}
                  aria-hidden="true"
                />
                Preflight repair
              </button>
            ) : (
              <div className="resolution-review">
                <dl>
                  <div>
                    <dt>Failure</dt>
                    <dd>{repairQuote.failure.failureCode}</dd>
                  </div>
                  <div>
                    <dt>Failed version</dt>
                    <dd>{repairQuote.failure.failedRecordVersion}</dd>
                  </div>
                  <div>
                    <dt>New version</dt>
                    <dd>{repairQuote.attestation.recordVersion}</dd>
                  </div>
                  <div>
                    <dt>Issuer</dt>
                    <dd>{repairQuote.attestation.issuerAddress}</dd>
                  </div>
                </dl>

                <button
                  className="mission-primary-button"
                  type="button"
                  disabled={
                    repairBusy
                    || repairProgress !== null
                  }
                  onClick={signRepair}
                >
                  <WalletCards
                    size={17}
                    aria-hidden="true"
                  />
                  Sign &amp; repair evidence
                </button>
              </div>
            )}

            {verifiedRepair !== null ? (
              <div className="resolution-success">
                Finalized repair verified · active record v
                {verifiedRepair.activeRecordVersion}.
              </div>
            ) : null}

            {repairError !== null ? (
              <p
                className="mission-error"
                role="alert"
              >
                {repairError}
              </p>
            ) : null}
          </article>

          <article>
            <div className="resolution-card-title">
              <ShieldAlert
                size={18}
                aria-hidden="true"
              />
              <div>
                <p>03 / RECOVERY</p>
                <h3>Abort and allocate refund after the hard deadline.</h3>
              </div>
            </div>

            <div className="resolution-warning">
              <CircleAlert
                size={17}
                aria-hidden="true"
              />
              Recovery is permissionless only after the mission recovery
              deadline. It can recover PREPARING, SEALED, or DECISION_PENDING
              value paths so funds cannot remain locked indefinitely.
            </div>

            {expireQuote === null ? (
              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  expireBusy
                  || missionId.length === 0
                }
                onClick={reviewExpiry}
              >
                <ArrowRight
                  size={17}
                  aria-hidden="true"
                />
                Preflight deadline recovery
              </button>
            ) : (
              <div className="resolution-review">
                <dl>
                  <div>
                    <dt>Current state</dt>
                    <dd>{expireQuote.mission.state}</dd>
                  </div>
                  <div>
                    <dt>Recovery deadline</dt>
                    <dd>{expireQuote.mission.recoveryDeadline}</dd>
                  </div>
                  <div>
                    <dt>Quoted fee</dt>
                    <dd>
                      {formatGenAmount(
                        expireQuote.feeValue,
                      )} GEN
                    </dd>
                  </div>
                </dl>

                <button
                  className="mission-primary-button"
                  type="button"
                  disabled={
                    expireBusy
                    || expireProgress !== null
                  }
                  onClick={signExpiry}
                >
                  <WalletCards
                    size={17}
                    aria-hidden="true"
                  />
                  Sign &amp; expire mission
                </button>
              </div>
            )}

            {expireProgress !== null ? (
              <div className="resolution-progress">
                <span>{expireProgress.phase}</span>
                <code>{expireProgress.txId}</code>
              </div>
            ) : null}

            {expireError !== null ? (
              <p
                className="mission-error"
                role="alert"
              >
                {expireError}
              </p>
            ) : null}
          </article>
        </div>

        <div className="resolution-allocation-note">
          <strong>Allocation truth boundary</strong>
          <p>
            The wallet never calls apply_decision directly. That method is
            self-only. COMMIT reports allocation complete only when a finalized
            coordinator reread shows COMMITTED or ABORTED with
            allocation_applied=true and the receipt carries the exact decision,
            reason, roots, nonce, and entitlement state.
          </p>
        </div>
      </div>
    </section>
  );
}
