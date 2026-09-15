"use client";

import {
  ArrowRight,
  Fingerprint,
  Link2,
  LoaderCircle,
  LockKeyhole,
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
  quoteSealMission,
  submitSealMission,
  verifyFinalizedSeal,
  type SealMissionQuote,
  type SealMissionSnapshot,
} from "@/lib/genlayer-seal";

type SealMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

export function SealMissionFlow({
  wallet,
  initialMissionId = "",
}: SealMissionFlowProps) {
  const [
    missionId,
    setMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    quote,
    setQuote,
  ] = useState<SealMissionQuote | null>(
    null,
  );
  const [
    progress,
    setProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    verifiedMission,
    setVerifiedMission,
  ] = useState<SealMissionSnapshot | null>(
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

  function resetReview() {
    setQuote(null);
    setProgress(null);
    setVerifiedMission(null);
    setError(null);
  }

  async function reviewSeal() {
    setBusy(true);
    setError(null);

    try {
      const next =
        await quoteSealMission(
          wallet,
          missionId,
        );

      setQuote(next);
    } catch (caught: unknown) {
      setQuote(null);
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to preflight mission sealing.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function signSeal() {
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
        await submitSealMission(
          wallet,
          quote,
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
        const finalized =
          await verifyFinalizedSeal(
            wallet,
            missionId,
            quote.roots.effectRoot,
            quote.roots.evidenceRoot,
          );

        setVerifiedMission(finalized);
      }
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Mission sealing failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="seal-flow">
      <div className="seal-flow-heading">
        <div>
          <p>SEAL / MISSION</p>
          <h2>
            Freeze exact effects and corroborated evidence into contract-derived roots.
          </h2>
        </div>
        <span>
          PRINCIPAL / FINAL PREPARATION WRITE
        </span>
      </div>

      <div className="seal-panel">
        <div className="seal-panel-title">
          <LockKeyhole
            size={21}
            aria-hidden="true"
          />
          <div>
            <p>ROOT / BINDING</p>
            <h3>
              Review final prepared state before locking the mission.
            </h3>
          </div>
        </div>

        <label className="seal-mission-input">
          <span>Mission ID</span>
          <input
            value={missionId}
            onChange={(event) => {
              setMissionId(
                event.target.value,
              );
              resetReview();
            }}
            placeholder="Mission ID"
            maxLength={512}
          />
        </label>

        <div className="seal-rule-grid">
          <div>
            <ShieldCheck
              size={17}
              aria-hidden="true"
            />
            <strong>Corroboration</strong>
            <span>
              At least two registered evidence records with distinct issuer
              identities and a contract-verified independent authority pair.
            </span>
          </div>
          <div>
            <Link2
              size={17}
              aria-hidden="true"
            />
            <strong>Effect graph</strong>
            <span>
              Every dependency must resolve and the prepared effect graph must
              remain acyclic.
            </span>
          </div>
          <div>
            <Fingerprint
              size={17}
              aria-hidden="true"
            />
            <strong>Exact roots</strong>
            <span>
              Roots are derived by the deployed coordinator from finalized
              state. The browser does not reimplement the hashing algorithm.
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
            onClick={reviewSeal}
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
            Preflight seal
          </button>
        ) : (
          <div className="seal-review">
            <dl>
              <div>
                <dt>Mission state</dt>
                <dd>{quote.mission.state}</dd>
              </div>
              <div>
                <dt>Mission version</dt>
                <dd>{quote.mission.version}</dd>
              </div>
              <div>
                <dt>Effects</dt>
                <dd>{quote.effects.length}</dd>
              </div>
              <div>
                <dt>Evidence</dt>
                <dd>{quote.evidence.length}</dd>
              </div>
              <div>
                <dt>Funded / prepared</dt>
                <dd>
                  {formatGenAmount(
                    quote.mission.fundedValue,
                  )} /{" "}
                  {formatGenAmount(
                    quote.mission.preparedValue,
                  )} GEN
                </dd>
              </div>
              <div>
                <dt>Independent authorities</dt>
                <dd>
                  {quote.independentPair.authorityA}
                  {" ↔ "}
                  {quote.independentPair.authorityB}
                </dd>
              </div>
              <div>
                <dt>Distinct issuers</dt>
                <dd>
                  {quote.independentPair.issuerA}
                  {" ↔ "}
                  {quote.independentPair.issuerB}
                </dd>
              </div>
              <div className="seal-root-row">
                <dt>Effect root</dt>
                <dd>
                  <code>
                    {quote.roots.effectRoot}
                  </code>
                </dd>
              </div>
              <div className="seal-root-row">
                <dt>Evidence root</dt>
                <dd>
                  <code>
                    {quote.roots.evidenceRoot}
                  </code>
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

            <div className="seal-final-warning">
              Sealing freezes the prepared effect and evidence roots. This
              transaction sends no mission value; the wallet only funds the
              quoted GenLayer transaction fee.
            </div>

            <button
              className="mission-primary-button"
              type="button"
              disabled={
                busy
                || progress !== null
              }
              onClick={signSeal}
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
              Sign &amp; seal mission
            </button>
          </div>
        )}

        {progress !== null ? (
          <div className="seal-progress">
            <span>{progress.phase}</span>
            <code>{progress.txId}</code>
            {verifiedMission !== null ? (
              <strong>
                Finalized SEALED state verified with the exact reviewed roots.
              </strong>
            ) : null}
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
