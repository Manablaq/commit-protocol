"use client";

import {
  ArrowRight,
  CircleCheck,
  CircleDashed,
  FileCheck2,
  Gavel,
  LoaderCircle,
  Scale,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import {
  formatGenAmount,
  readMissionEvidence,
  type ConnectedCommitWallet,
  type EvidenceSnapshot,
} from "@/lib/genlayer-browser";
import {
  readMissionReceipt,
  readResolutionMission,
  type MissionReceiptSnapshot,
  type ResolutionMissionSnapshot,
} from "@/lib/genlayer-resolution";
import {
  appealCommitTransaction,
  readAppealLifecycle,
  type AppealLifecycleSnapshot,
} from "@/lib/genlayer-appeal";
import { AppealPanel } from "@/components/justice/appeal-panel";
import { EvidenceRecordCard } from "@/components/justice/evidence-record-card";

type CaseRoomProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

type CaseData = {
  mission: ResolutionMissionSnapshot;
  receipt: MissionReceiptSnapshot;
  evidence: EvidenceSnapshot[];
  appeal: AppealLifecycleSnapshot | null;
};

type TimelineStep = {
  label: string;
  description: string;
  complete: boolean;
  active: boolean;
};

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The Case Room could not read the requested protocol state.";
}

function shorten(value: string): string {
  return value.length > 22
    ? `${value.slice(0, 10)}…${value.slice(-8)}`
    : value;
}

function stateIsSealed(mission: ResolutionMissionSnapshot): boolean {
  return [
    "SEALED",
    "DECISION_PENDING",
    "COMMITTED",
    "ABORTED",
  ].includes(mission.state);
}

function timelineFor(
  data: CaseData,
): TimelineStep[] {
  const decisionExists = data.mission.decision.length > 0;
  const finalVerdict = data.appeal?.phase === "FINALIZED";
  const appealOpen = data.appeal?.phase === "APPEAL_OPEN";
  const appealInProgress = data.appeal?.phase === "APPEAL_IN_PROGRESS";

  return [
    {
      label: "Agreement created",
      description: "Terms and economic intent exist on the coordinator.",
      complete: true,
      active: false,
    },
    {
      label: "Escrow funded",
      description: "Value is held against the declared agreement budget.",
      complete: data.receipt.fundedValue > BigInt(0),
      active: data.receipt.fundedValue <= BigInt(0),
    },
    {
      label: "Evidence bound",
      description: "Authenticated, versioned evidence is registered.",
      complete: data.evidence.length > 0,
      active: data.evidence.length === 0,
    },
    {
      label: "Terms sealed",
      description: "The mission, effect root, and evidence root are frozen.",
      complete: stateIsSealed(data.mission),
      active: data.mission.state === "PREPARING" && data.evidence.length > 0,
    },
    {
      label: "Evidence review",
      description: "GenLayer validators are evaluating the bound records.",
      complete: decisionExists,
      active: stateIsSealed(data.mission) && !decisionExists,
    },
    {
      label: "Provisional verdict",
      description: "A decision exists but can still be appealed.",
      complete: decisionExists && !finalVerdict,
      active: decisionExists && !finalVerdict,
    },
    {
      label: appealInProgress ? "Appeal in progress" : "Appeal window",
      description: appealInProgress
        ? "A fresh committee is rechecking the active decision."
        : "The protocol controls whether a decision can still be challenged.",
      complete: appealOpen || appealInProgress || finalVerdict,
      active: appealOpen || appealInProgress,
    },
    {
      label: "Final verdict",
      description: "Only finality makes the evaluated outcome durable.",
      complete: finalVerdict,
      active: finalVerdict,
    },
    {
      label: data.mission.decision === "COMMIT" ? "Supplier award" : "Buyer refund",
      description: data.mission.allocationApplied
        ? "The finalized self-callback applied the declared consequence."
        : "The economic consequence remains unapplied until finality.",
      complete: data.mission.allocationApplied,
      active: data.mission.allocationApplied,
    },
  ];
}

export function CaseRoom({
  wallet,
  initialMissionId = "",
}: CaseRoomProps) {
  const [missionId, setMissionId] = useState(initialMissionId);
  const [evaluationTxId, setEvaluationTxId] = useState(() => {
    if (typeof window === "undefined" || initialMissionId.length === 0) {
      return "";
    }

    return window.localStorage.getItem(
      `commit:evaluation:${initialMissionId}`,
    ) ?? "";
  });
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appealLoading, setAppealLoading] = useState(false);
  const [appealBusy, setAppealBusy] = useState(false);
  const [appealError, setAppealError] = useState<string | null>(null);
  const [submittedAppeal, setSubmittedAppeal] = useState<string | null>(null);

  const timeline = useMemo(
    () => caseData === null ? [] : timelineFor(caseData),
    [caseData],
  );

  async function refreshCase() {
    if (missionId.trim().length === 0) {
      setError("Enter a mission ID before reading a case.");
      return;
    }

    setLoading(true);
    setAppealLoading(evaluationTxId.trim().length > 0);
    setError(null);
    setAppealError(null);

    try {
      const [mission, receipt, evidence] = await Promise.all([
        readResolutionMission(wallet, missionId.trim()),
        readMissionReceipt(wallet, missionId.trim()),
        readMissionEvidence(wallet, missionId.trim()),
      ]);

      let appeal: AppealLifecycleSnapshot | null = null;

      if (evaluationTxId.trim().length > 0) {
        try {
          appeal = await readAppealLifecycle(
            wallet.client,
            evaluationTxId.trim(),
          );
        } catch (appealReadError: unknown) {
          setAppealError(errorMessage(appealReadError));
        }
      }

      setCaseData({
        mission,
        receipt,
        evidence,
        appeal,
      });
    } catch (caught: unknown) {
      setCaseData(null);
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
      setAppealLoading(false);
    }
  }

  async function submitAppeal() {
    if (
      caseData?.appeal === null
      || caseData?.appeal === undefined
      || !caseData.appeal.canAppeal
      || evaluationTxId.trim().length === 0
    ) {
      return;
    }

    setAppealBusy(true);
    setAppealError(null);

    try {
      const txId = await appealCommitTransaction(
        wallet,
        evaluationTxId.trim(),
      );

      setSubmittedAppeal(txId);
      setAppealBusy(false);
      void refreshCase();
    } catch (caught: unknown) {
      setAppealError(errorMessage(caught));
      setAppealBusy(false);
    }
  }

  return (
    <section className="justice-case-room" id="case-room">
      <div className="justice-section-heading">
        <div>
          <p>ONCHAIN JUSTICE / CASE ROOM</p>
          <h2>Make a machine-settled dispute legible.</h2>
        </div>
        <span>REAL CONTRACT STATE · REAL GENLAYER LIFECYCLE</span>
      </div>

      <div className="justice-case-controls">
        <label>
          <span>Mission / agreement ID</span>
          <input
            value={missionId}
            onChange={(event) => {
              const nextMissionId = event.target.value;
              setMissionId(nextMissionId);
              setEvaluationTxId(
                typeof window === "undefined"
                  ? ""
                  : window.localStorage.getItem(
                      `commit:evaluation:${nextMissionId}`,
                    ) ?? "",
              );
              setCaseData(null);
              setError(null);
            }}
            placeholder="e.g. api-delivery-001"
            maxLength={512}
          />
        </label>
        <label>
          <span>Evaluation transaction ID</span>
          <input
            value={evaluationTxId}
            onChange={(event) => {
              setEvaluationTxId(event.target.value);
              setCaseData((current) => current === null
                ? null
                : { ...current, appeal: null });
              setAppealError(null);
            }}
            placeholder="0x… exact GenLayer evaluation tx"
            spellCheck={false}
          />
        </label>
        <button
          className="mission-primary-button justice-read-button"
          type="button"
          onClick={refreshCase}
          disabled={loading}
        >
          {loading ? (
            <LoaderCircle className="spin" size={17} aria-hidden="true" />
          ) : (
            <ArrowRight size={17} aria-hidden="true" />
          )}
          {loading ? "Reading case…" : "Open case room"}
        </button>
      </div>

      {error !== null ? (
        <div className="justice-error" role="alert">
          <ShieldCheck size={16} aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}

      {caseData === null ? (
        <div className="justice-case-empty">
          <Scale size={34} aria-hidden="true" />
          <div>
            <strong>Open a real agreement to begin.</strong>
            <p>
              The Case Room reads the deployed coordinator at {shorten(wallet.address)}.
              It never invents an appeal, verdict, or payment state.
            </p>
          </div>
        </div>
      ) : (
        <>
          <div className="justice-case-overview">
            <div className="justice-case-title">
              <span className="justice-live-label">
                <CircleCheck size={14} aria-hidden="true" />
                Live agreement
              </span>
              <h3>{caseData.mission.missionId}</h3>
              <p>{caseData.receipt.protocol} · {caseData.receipt.revision}</p>
            </div>
            <div className="justice-case-metrics">
              <div>
                <span>Escrow</span>
                <strong>{formatGenAmount(caseData.receipt.fundedValue)} GEN</strong>
              </div>
              <div>
                <span>Policy</span>
                <strong>{caseData.mission.state}</strong>
              </div>
              <div>
                <span>Decision</span>
                <strong>{caseData.mission.decision || "Under review"}</strong>
              </div>
              <div>
                <span>Consequence</span>
                <strong>{caseData.mission.allocationApplied ? "Allocated" : "Waiting"}</strong>
              </div>
            </div>
          </div>

          <div className="justice-case-grid">
            <article className="justice-panel justice-timeline-panel">
              <div className="justice-panel-heading">
                <div>
                  <p className="card-kicker">Case timeline</p>
                  <h3>Agreement → finality → enforcement</h3>
                </div>
                <Gavel size={20} aria-hidden="true" />
              </div>
              <div className="justice-timeline">
                {timeline.map((step) => (
                  <div
                    className={`justice-timeline-step ${step.complete ? "is-complete" : ""} ${step.active ? "is-active" : ""}`}
                    key={step.label}
                  >
                    <span className="justice-timeline-marker" aria-hidden="true">
                      {step.complete ? <CircleCheck size={15} /> : <CircleDashed size={15} />}
                    </span>
                    <div>
                      <strong>{step.label}</strong>
                      <span>{step.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <AppealPanel
              snapshot={caseData.appeal}
              loading={appealLoading}
              busy={appealBusy}
              error={appealError}
              submittedTxId={submittedAppeal}
              onRefresh={() => {
                setAppealLoading(true);
                void refreshCase().finally(() => setAppealLoading(false));
              }}
              onAppeal={submitAppeal}
            />
          </div>

          <div className="justice-case-grid justice-case-grid-bottom">
            <article className="justice-panel evidence-panel">
              <div className="justice-panel-heading">
                <div>
                  <p className="card-kicker">Evidence register</p>
                  <h3>{caseData.evidence.length} authenticated records</h3>
                </div>
                <FileCheck2 size={20} aria-hidden="true" />
              </div>
              <div className="evidence-record-list">
                {caseData.evidence.length === 0 ? (
                  <div className="justice-empty-copy">
                    <p>No evidence is registered in this agreement yet.</p>
                  </div>
                ) : (
                  caseData.evidence.map((evidence) => (
                    <EvidenceRecordCard
                      evidence={evidence}
                      missionVersion={caseData.mission.version}
                      key={evidence.evidenceId}
                    />
                  ))
                )}
              </div>
            </article>

            <article className="justice-panel settlement-panel">
              <div className="justice-panel-heading">
                <div>
                  <p className="card-kicker">Settlement consequence</p>
                  <h3>
                    {caseData.mission.decision === "COMMIT"
                      ? "Supplier award"
                      : caseData.mission.decision === "ABORT"
                        ? "Buyer refund"
                        : "No consequence yet"}
                  </h3>
                </div>
                <WalletCards size={20} aria-hidden="true" />
              </div>
              <div className="settlement-amount">
                <span>Prepared value</span>
                <strong>{formatGenAmount(caseData.receipt.preparedValue)} GEN</strong>
              </div>
              <p>
                COMMIT exposes a consequence only after the finalized
                decision callback applies the exact sealed effect root. A
                provisional verdict never appears here as paid.
              </p>
              <dl className="justice-fact-grid">
                <div>
                  <dt>Allocation</dt>
                  <dd>{caseData.mission.allocationApplied ? "Applied once" : "Not applied"}</dd>
                </div>
                <div>
                  <dt>Refund entitlement</dt>
                  <dd>{formatGenAmount(caseData.mission.refundEntitlement)} GEN</dd>
                </div>
                <div>
                  <dt>Effect root</dt>
                  <dd>{shorten(caseData.mission.effectRoot)}</dd>
                </div>
                <div>
                  <dt>Evidence root</dt>
                  <dd>{shorten(caseData.mission.evidenceRoot)}</dd>
                </div>
              </dl>
            </article>
          </div>
        </>
      )}
    </section>
  );
}
