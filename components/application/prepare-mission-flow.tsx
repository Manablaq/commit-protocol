"use client";

import {
  ArrowRight,
  LoaderCircle,
  Network,
  UserPlus,
  WalletCards,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  formatGenAmount,
  quotePrepareEffect,
  quoteSupplierAuthorization,
  readMissionEffects,
  readSupplierAuthorization,
  submitPrepareEffect,
  submitSupplierAuthorization,
  trackCommitTransaction,
  type ConnectedCommitWallet,
  type PrepareEffectQuote,
  type SupplierAuthorizationQuote,
  type TransactionProgress,
} from "@/lib/genlayer-browser";

type PrepareMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

function defaultExpiry(): string {
  const date = new Date(
    Date.now()
    + 8 * 24 * 60 * 60 * 1000,
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
  const milliseconds =
    new Date(
      value,
    ).getTime();

  if (!Number.isFinite(
    milliseconds,
  )) {
    return 0;
  }

  return Math.floor(
    milliseconds / 1000,
  );
}

export function PrepareMissionFlow({
  wallet,
  initialMissionId = "",
}: PrepareMissionFlowProps) {
  const [
    supplierMissionId,
    setSupplierMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    supplierAddress,
    setSupplierAddress,
  ] = useState("");
  const [
    supplierQuote,
    setSupplierQuote,
  ] = useState<SupplierAuthorizationQuote | null>(
    null,
  );
  const [
    supplierProgress,
    setSupplierProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    supplierVerified,
    setSupplierVerified,
  ] = useState<boolean | null>(
    null,
  );
  const [
    supplierBusy,
    setSupplierBusy,
  ] = useState(false);
  const [
    supplierError,
    setSupplierError,
  ] = useState<string | null>(
    null,
  );

  const [
    missionId,
    setMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    effectId,
    setEffectId,
  ] = useState("");
  const [
    effectDigest,
    setEffectDigest,
  ] = useState("");
  const [
    beneficiary,
    setBeneficiary,
  ] = useState<string>(
    wallet.address,
  );
  const [
    valueGen,
    setValueGen,
  ] = useState("");
  const [
    expiryAt,
    setExpiryAt,
  ] = useState(
    defaultExpiry,
  );
  const [
    dependencyId,
    setDependencyId,
  ] = useState("");
  const [
    effectQuote,
    setEffectQuote,
  ] = useState<PrepareEffectQuote | null>(
    null,
  );
  const [
    effectProgress,
    setEffectProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    effectVerified,
    setEffectVerified,
  ] = useState(false);
  const [
    effectBusy,
    setEffectBusy,
  ] = useState(false);
  const [
    effectError,
    setEffectError,
  ] = useState<string | null>(
    null,
  );

  function resetSupplierReview() {
    setSupplierQuote(
      null,
    );
    setSupplierProgress(
      null,
    );
    setSupplierVerified(
      null,
    );
    setSupplierError(
      null,
    );
  }

  function resetEffectReview() {
    setEffectQuote(
      null,
    );
    setEffectProgress(
      null,
    );
    setEffectVerified(
      false,
    );
    setEffectError(
      null,
    );
  }

  async function reviewSupplierAuthorization() {
    setSupplierBusy(
      true,
    );
    setSupplierError(
      null,
    );

    try {
      const quote =
        await quoteSupplierAuthorization(
          wallet,
          supplierMissionId,
          supplierAddress,
        );

      setSupplierQuote(
        quote,
      );
    } catch (error: unknown) {
      setSupplierQuote(
        null,
      );
      setSupplierError(
        error instanceof Error
          ? error.message
          : "Unable to preflight supplier authorization.",
      );
    } finally {
      setSupplierBusy(
        false,
      );
    }
  }

  async function signSupplierAuthorization() {
    if (
      supplierQuote === null
      || supplierBusy
    ) {
      return;
    }

    setSupplierBusy(
      true,
    );
    setSupplierError(
      null,
    );

    try {
      const txId =
        await submitSupplierAuthorization(
          wallet,
          supplierQuote,
        );

      setSupplierProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setSupplierProgress,
        );

      if (result.successful) {
        const authorized =
          await readSupplierAuthorization(
            wallet,
            supplierMissionId,
            supplierAddress,
          );

        setSupplierVerified(
          authorized,
        );
      }
    } catch (error: unknown) {
      setSupplierError(
        error instanceof Error
          ? error.message
          : "Supplier authorization failed.",
      );
    } finally {
      setSupplierBusy(
        false,
      );
    }
  }

  async function reviewEffect() {
    setEffectBusy(
      true,
    );
    setEffectError(
      null,
    );

    try {
      const quote =
        await quotePrepareEffect(
          wallet,
          {
            missionId,
            effectId,
            effectDigest,
            beneficiary,
            valueGen,
            expiry:
              unixTimestamp(
                expiryAt,
              ),
            dependencyId,
          },
        );

      setEffectQuote(
        quote,
      );
    } catch (error: unknown) {
      setEffectQuote(
        null,
      );
      setEffectError(
        error instanceof Error
          ? error.message
          : "Unable to preflight effect preparation.",
      );
    } finally {
      setEffectBusy(
        false,
      );
    }
  }

  async function signEffect() {
    if (
      effectQuote === null
      || effectBusy
    ) {
      return;
    }

    setEffectBusy(
      true,
    );
    setEffectError(
      null,
    );

    try {
      const txId =
        await submitPrepareEffect(
          wallet,
          effectQuote,
        );

      setEffectProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setEffectProgress,
        );

      if (result.successful) {
        const effects =
          await readMissionEffects(
            wallet,
            missionId,
          );

        setEffectVerified(
          effects.some(
            (effect) => (
              effect.effectId
              === effectId
            ),
          ),
        );
      }
    } catch (error: unknown) {
      setEffectError(
        error instanceof Error
          ? error.message
          : "Effect preparation failed.",
      );
    } finally {
      setEffectBusy(
        false,
      );
    }
  }

  return (
    <section className="prepare-flow">
      <div className="prepare-flow-heading">
        <div>
          <p>PREPARE / MISSION</p>
          <h2>
            Authorize who may prepare consequences, then bind exact effects.
          </h2>
        </div>
        <span>
          FINAL-STATE PREFLIGHT
        </span>
      </div>

      <div className="prepare-flow-grid">
        <article className="prepare-panel">
          <div className="prepare-panel-title">
            <UserPlus
              size={20}
              aria-hidden="true"
            />
            <div>
              <p>AUTHORIZE / SUPPLIER</p>
              <h3>
                Principal-controlled supplier access
              </h3>
            </div>
          </div>

          <label>
            <span>Mission ID</span>
            <input
              value={supplierMissionId}
              onChange={(event) => {
                setSupplierMissionId(
                  event.target.value,
                );
                resetSupplierReview();
              }}
              placeholder="Mission ID"
              maxLength={512}
            />
          </label>

          <label>
            <span>Supplier address</span>
            <input
              value={supplierAddress}
              onChange={(event) => {
                setSupplierAddress(
                  event.target.value,
                );
                resetSupplierReview();
              }}
              placeholder="0x..."
              spellCheck={false}
            />
          </label>

          <div className="prepare-rule-note">
            Only the mission principal can authorize a supplier. The mission
            must still be PREPARING and inside its preparation window.
          </div>

          {supplierQuote === null ? (
            <button
              className="mission-primary-button"
              type="button"
              disabled={
                supplierBusy
                || supplierMissionId.length === 0
                || supplierAddress.length === 0
              }
              onClick={reviewSupplierAuthorization}
            >
              {supplierBusy ? (
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
              Preflight supplier
            </button>
          ) : (
            <div className="prepare-review">
              <dl>
                <div>
                  <dt>Mission state</dt>
                  <dd>
                    {supplierQuote.mission.state}
                  </dd>
                </div>
                <div>
                  <dt>Principal</dt>
                  <dd>
                    {supplierQuote.mission.principal}
                  </dd>
                </div>
                <div>
                  <dt>Supplier</dt>
                  <dd>
                    {supplierQuote.supplier}
                  </dd>
                </div>
                <div>
                  <dt>Quoted fee</dt>
                  <dd>
                    {formatGenAmount(
                      supplierQuote.feeValue,
                    )} GEN
                  </dd>
                </div>
              </dl>

              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  supplierBusy
                  || supplierProgress !== null
                }
                onClick={signSupplierAuthorization}
              >
                {supplierBusy ? (
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
                Sign &amp; authorize supplier
              </button>
            </div>
          )}

          {supplierProgress !== null ? (
            <div className="prepare-progress">
              <span>
                {supplierProgress.phase}
              </span>
              <code>
                {supplierProgress.txId}
              </code>
              {supplierVerified === true ? (
                <strong>
                  Supplier authorization verified in finalized state.
                </strong>
              ) : null}
            </div>
          ) : null}

          {supplierError !== null ? (
            <p
              className="mission-error"
              role="alert"
            >
              {supplierError}
            </p>
          ) : null}
        </article>

        <article className="prepare-panel prepare-panel-effect">
          <div className="prepare-panel-title">
            <Network
              size={20}
              aria-hidden="true"
            />
            <div>
              <p>PREPARE / EFFECT</p>
              <h3>
                Bind an exact consequence allocation
              </h3>
            </div>
          </div>

          <div className="prepare-effect-form">
            <label>
              <span>Mission ID</span>
              <input
                value={missionId}
                onChange={(event) => {
                  setMissionId(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="Mission ID"
                maxLength={512}
              />
            </label>

            <label>
              <span>Effect ID</span>
              <input
                value={effectId}
                onChange={(event) => {
                  setEffectId(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="effect-001"
                maxLength={512}
              />
            </label>

            <label className="prepare-field-wide">
              <span>Effect digest · 32-byte lowercase hex</span>
              <input
                value={effectDigest}
                onChange={(event) => {
                  setEffectDigest(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="64 lowercase hexadecimal characters"
                spellCheck={false}
                maxLength={64}
              />
            </label>

            <label>
              <span>Beneficiary</span>
              <input
                value={beneficiary}
                onChange={(event) => {
                  setBeneficiary(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="0x..."
                spellCheck={false}
              />
            </label>

            <label>
              <span>Effect value · GEN allocation</span>
              <input
                value={valueGen}
                onChange={(event) => {
                  setValueGen(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="0.5"
                inputMode="decimal"
              />
            </label>

            <label>
              <span>Effect expiry</span>
              <input
                type="datetime-local"
                value={expiryAt}
                onChange={(event) => {
                  setExpiryAt(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
              />
            </label>

            <label>
              <span>Dependency effect ID · optional</span>
              <input
                value={dependencyId}
                onChange={(event) => {
                  setDependencyId(
                    event.target.value,
                  );
                  resetEffectReview();
                }}
                placeholder="existing-effect-id"
                maxLength={512}
              />
            </label>
          </div>

          <div className="prepare-rule-note">
            Effect value is a semantic allocation against the mission budget,
            not a payable GEN transfer. Only the quoted transaction fee is a
            wallet cost at this step.
          </div>

          {effectQuote === null ? (
            <button
              className="mission-primary-button"
              type="button"
              disabled={
                effectBusy
                || missionId.length === 0
                || effectId.length === 0
                || effectDigest.length === 0
                || beneficiary.length === 0
                || valueGen.length === 0
              }
              onClick={reviewEffect}
            >
              {effectBusy ? (
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
              Preflight effect
            </button>
          ) : (
            <div className="prepare-review">
              <dl>
                <div>
                  <dt>Mission state</dt>
                  <dd>
                    {effectQuote.mission.state}
                  </dd>
                </div>
                <div>
                  <dt>Prepared / budget</dt>
                  <dd>
                    {formatGenAmount(
                      effectQuote.mission.preparedValue,
                    )} /{" "}
                    {formatGenAmount(
                      effectQuote.mission.budget,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Effect allocation</dt>
                  <dd>
                    {formatGenAmount(
                      effectQuote.value,
                    )} GEN
                  </dd>
                </div>
                <div>
                  <dt>Existing effects</dt>
                  <dd>
                    {effectQuote.existingEffects.length}
                  </dd>
                </div>
                <div>
                  <dt>Dependency</dt>
                  <dd>
                    {dependencyId || "None"}
                  </dd>
                </div>
                <div>
                  <dt>Quoted fee</dt>
                  <dd>
                    {formatGenAmount(
                      effectQuote.feeValue,
                    )} GEN
                  </dd>
                </div>
              </dl>

              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  effectBusy
                  || effectProgress !== null
                }
                onClick={signEffect}
              >
                {effectBusy ? (
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
                Sign &amp; prepare effect
              </button>
            </div>
          )}

          {effectProgress !== null ? (
            <div className="prepare-progress">
              <span>
                {effectProgress.phase}
              </span>
              <code>
                {effectProgress.txId}
              </code>
              {effectVerified ? (
                <strong>
                  Effect verified in finalized mission state.
                </strong>
              ) : null}
            </div>
          ) : null}

          {effectError !== null ? (
            <p
              className="mission-error"
              role="alert"
            >
              {effectError}
            </p>
          ) : null}
        </article>
      </div>
    </section>
  );
}
