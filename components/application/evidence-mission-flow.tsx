"use client";

import {
  ArrowRight,
  BadgeCheck,
  FileCheck2,
  LoaderCircle,
  WalletCards,
} from "lucide-react";
import {
  useState,
} from "react";
import {
  formatGenAmount,
  quoteAttestEvidence,
  quoteRegisterEvidence,
  readEvidence,
  readEvidenceAttestation,
  submitEvidenceAttestation,
  submitEvidenceRegistration,
  trackCommitTransaction,
  type AttestEvidenceQuote,
  type ConnectedCommitWallet,
  type EvidenceAttestationSnapshot,
  type EvidenceSnapshot,
  type RegisterEvidenceQuote,
  type TransactionProgress,
} from "@/lib/genlayer-browser";

type EvidenceMissionFlowProps = {
  wallet: ConnectedCommitWallet;
  initialMissionId?: string;
};

function localDateTime(
  milliseconds: number,
): string {
  const date =
    new Date(
      milliseconds,
    );

  const local =
    new Date(
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

function positiveInteger(
  value: string,
): number {
  if (
    !/^[1-9][0-9]*$/.test(
      value,
    )
  ) {
    return 0;
  }

  const parsed =
    Number(
      value,
    );

  return Number.isSafeInteger(
    parsed,
  )
    ? parsed
    : 0;
}

export function EvidenceMissionFlow({
  wallet,
  initialMissionId = "",
}: EvidenceMissionFlowProps) {
  const [
    attestMissionId,
    setAttestMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    attestAuthorityId,
    setAttestAuthorityId,
  ] = useState("");
  const [
    attestRecordId,
    setAttestRecordId,
  ] = useState("");
  const [
    attestRecordVersion,
    setAttestRecordVersion,
  ] = useState("1");
  const [
    attestUrl,
    setAttestUrl,
  ] = useState("");
  const [
    attestRecordHash,
    setAttestRecordHash,
  ] = useState("");
  const [
    publishedAt,
    setPublishedAt,
  ] = useState(
    () => localDateTime(
      Date.now(),
    ),
  );
  const [
    expiresAt,
    setExpiresAt,
  ] = useState(
    () => localDateTime(
      Date.now()
      + 8 * 24 * 60 * 60 * 1000,
    ),
  );
  const [
    attestQuote,
    setAttestQuote,
  ] = useState<AttestEvidenceQuote | null>(
    null,
  );
  const [
    attestProgress,
    setAttestProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    verifiedAttestation,
    setVerifiedAttestation,
  ] = useState<EvidenceAttestationSnapshot | null>(
    null,
  );
  const [
    attestBusy,
    setAttestBusy,
  ] = useState(false);
  const [
    attestError,
    setAttestError,
  ] = useState<string | null>(
    null,
  );

  const [
    registerMissionId,
    setRegisterMissionId,
  ] = useState(
    initialMissionId,
  );
  const [
    evidenceId,
    setEvidenceId,
  ] = useState("");
  const [
    registerAuthorityId,
    setRegisterAuthorityId,
  ] = useState("");
  const [
    registerRecordId,
    setRegisterRecordId,
  ] = useState("");
  const [
    registerRecordVersion,
    setRegisterRecordVersion,
  ] = useState("1");
  const [
    registerQuote,
    setRegisterQuote,
  ] = useState<RegisterEvidenceQuote | null>(
    null,
  );
  const [
    registerProgress,
    setRegisterProgress,
  ] = useState<TransactionProgress | null>(
    null,
  );
  const [
    verifiedEvidence,
    setVerifiedEvidence,
  ] = useState<EvidenceSnapshot | null>(
    null,
  );
  const [
    registerBusy,
    setRegisterBusy,
  ] = useState(false);
  const [
    registerError,
    setRegisterError,
  ] = useState<string | null>(
    null,
  );

  function resetAttestation() {
    setAttestQuote(
      null,
    );
    setAttestProgress(
      null,
    );
    setVerifiedAttestation(
      null,
    );
    setAttestError(
      null,
    );
  }

  function resetRegistration() {
    setRegisterQuote(
      null,
    );
    setRegisterProgress(
      null,
    );
    setVerifiedEvidence(
      null,
    );
    setRegisterError(
      null,
    );
  }

  async function reviewAttestation() {
    setAttestBusy(
      true,
    );
    setAttestError(
      null,
    );

    try {
      const quote =
        await quoteAttestEvidence(
          wallet,
          {
            missionId:
              attestMissionId,
            authorityId:
              attestAuthorityId,
            recordId:
              attestRecordId,
            recordVersion:
              positiveInteger(
                attestRecordVersion,
              ),
            url:
              attestUrl,
            recordHash:
              attestRecordHash,
            publishedAt:
              unixTimestamp(
                publishedAt,
              ),
            expiresAt:
              unixTimestamp(
                expiresAt,
              ),
          },
        );

      setAttestQuote(
        quote,
      );
    } catch (error: unknown) {
      setAttestQuote(
        null,
      );
      setAttestError(
        error instanceof Error
          ? error.message
          : "Unable to preflight evidence attestation.",
      );
    } finally {
      setAttestBusy(
        false,
      );
    }
  }

  async function signAttestation() {
    if (
      attestQuote === null
      || attestBusy
    ) {
      return;
    }

    setAttestBusy(
      true,
    );
    setAttestError(
      null,
    );

    try {
      const txId =
        await submitEvidenceAttestation(
          wallet,
          attestQuote,
        );

      setAttestProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setAttestProgress,
        );

      if (result.successful) {
        const attestation =
          await readEvidenceAttestation(
            wallet,
            attestQuote.authority.authorityId,
            attestRecordId,
            positiveInteger(
              attestRecordVersion,
            ),
          );

        setVerifiedAttestation(
          attestation,
        );
      }
    } catch (error: unknown) {
      setAttestError(
        error instanceof Error
          ? error.message
          : "Evidence attestation failed.",
      );
    } finally {
      setAttestBusy(
        false,
      );
    }
  }

  async function reviewRegistration() {
    setRegisterBusy(
      true,
    );
    setRegisterError(
      null,
    );

    try {
      const quote =
        await quoteRegisterEvidence(
          wallet,
          {
            missionId:
              registerMissionId,
            evidenceId,
            authorityId:
              registerAuthorityId,
            recordId:
              registerRecordId,
            recordVersion:
              positiveInteger(
                registerRecordVersion,
              ),
          },
        );

      setRegisterQuote(
        quote,
      );
    } catch (error: unknown) {
      setRegisterQuote(
        null,
      );
      setRegisterError(
        error instanceof Error
          ? error.message
          : "Unable to preflight evidence registration.",
      );
    } finally {
      setRegisterBusy(
        false,
      );
    }
  }

  async function signRegistration() {
    if (
      registerQuote === null
      || registerBusy
    ) {
      return;
    }

    setRegisterBusy(
      true,
    );
    setRegisterError(
      null,
    );

    try {
      const txId =
        await submitEvidenceRegistration(
          wallet,
          registerQuote,
        );

      setRegisterProgress({
        phase: "submitted",
        txId,
      });

      const result =
        await trackCommitTransaction(
          txId,
          setRegisterProgress,
        );

      if (result.successful) {
        const evidence =
          await readEvidence(
            wallet,
            registerMissionId,
            evidenceId,
          );

        setVerifiedEvidence(
          evidence,
        );
      }
    } catch (error: unknown) {
      setRegisterError(
        error instanceof Error
          ? error.message
          : "Evidence registration failed.",
      );
    } finally {
      setRegisterBusy(
        false,
      );
    }
  }

  return (
    <section className="evidence-flow">
      <div className="evidence-flow-heading">
        <div>
          <p>EVIDENCE / BINDING</p>
          <h2>
            Attest provenance first. Register it into the mission second.
          </h2>
        </div>
        <span>
          ISSUER + PRINCIPAL ROLES
        </span>
      </div>

      <div className="evidence-role-grid">
        <article className="evidence-panel">
          <div className="evidence-panel-title">
            <BadgeCheck
              size={20}
              aria-hidden="true"
            />
            <div>
              <p>ISSUER / ATTEST</p>
              <h3>
                Bind immutable, versioned records to an approved authority.
              </h3>
            </div>
          </div>

          <div className="evidence-form-grid">
            <label>
              <span>Mission ID</span>
              <input
                value={attestMissionId}
                onChange={(event) => {
                  setAttestMissionId(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                placeholder="Mission ID"
                maxLength={512}
              />
            </label>

            <label>
              <span>Authority ID</span>
              <input
                value={attestAuthorityId}
                onChange={(event) => {
                  setAttestAuthorityId(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                placeholder="authority-id"
                maxLength={64}
              />
            </label>

            <label>
              <span>Record ID</span>
              <input
                value={attestRecordId}
                onChange={(event) => {
                  setAttestRecordId(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                placeholder="stable-record-id"
                maxLength={512}
              />
            </label>

            <label>
              <span>Record version</span>
              <input
                value={attestRecordVersion}
                onChange={(event) => {
                  setAttestRecordVersion(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                inputMode="numeric"
              />
            </label>

            <label className="evidence-field-wide">
              <span>Immutable/versioned evidence URL</span>
              <input
                value={attestUrl}
                onChange={(event) => {
                  setAttestUrl(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                placeholder="https://approved.example/path/record.json"
                spellCheck={false}
              />
            </label>

            <label className="evidence-field-wide">
              <span>Record hash · 32-byte lowercase hex</span>
              <input
                value={attestRecordHash}
                onChange={(event) => {
                  setAttestRecordHash(
                    event.target.value,
                  );
                  resetAttestation();
                }}
                placeholder="64 lowercase hexadecimal characters"
                spellCheck={false}
                maxLength={64}
              />
            </label>

            <label>
              <span>Published at</span>
              <input
                type="datetime-local"
                value={publishedAt}
                onChange={(event) => {
                  setPublishedAt(
                    event.target.value,
                  );
                  resetAttestation();
                }}
              />
            </label>

            <label>
              <span>Expires at</span>
              <input
                type="datetime-local"
                value={expiresAt}
                onChange={(event) => {
                  setExpiresAt(
                    event.target.value,
                  );
                  resetAttestation();
                }}
              />
            </label>
          </div>

          <div className="evidence-rule-note">
            The connected wallet must be the registered issuer. COMMIT checks
            the authority is active, the exact authority version, registered authority origin/path,
            mission version, record version, publication time, expiry, and
            lowercase 32-byte hash before signing.
          </div>

          {attestQuote === null ? (
            <button
              className="mission-primary-button"
              type="button"
              disabled={
                attestBusy
                || attestMissionId.length === 0
                || attestAuthorityId.length === 0
                || attestRecordId.length === 0
                || attestUrl.length === 0
                || attestRecordHash.length === 0
              }
              onClick={reviewAttestation}
            >
              {attestBusy ? (
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
              Preflight attestation
            </button>
          ) : (
            <div className="evidence-review">
              <dl>
                <div>
                  <dt>Authority</dt>
                  <dd>
                    {attestQuote.authority.authorityId}
                    {" · v"}
                    {attestQuote.authority.authorityVersion}
                  </dd>
                </div>
                <div>
                  <dt>Issuer</dt>
                  <dd>
                    {attestQuote.authority.issuerAddress}
                  </dd>
                </div>
                <div>
                  <dt>Authority scope</dt>
                  <dd>
                    https://{attestQuote.authority.host}
                    {attestQuote.authority.pathPrefix}
                  </dd>
                </div>
                <div>
                  <dt>Mission version</dt>
                  <dd>
                    {attestQuote.mission.version}
                  </dd>
                </div>
                <div>
                  <dt>Quoted fee</dt>
                  <dd>
                    {formatGenAmount(
                      attestQuote.feeValue,
                    )} GEN
                  </dd>
                </div>
              </dl>

              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  attestBusy
                  || attestProgress !== null
                }
                onClick={signAttestation}
              >
                {attestBusy ? (
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
                Sign &amp; attest evidence
              </button>
            </div>
          )}

          {attestProgress !== null ? (
            <div className="evidence-progress">
              <span>
                {attestProgress.phase}
              </span>
              <code>
                {attestProgress.txId}
              </code>
              {verifiedAttestation !== null ? (
                <strong>
                  Finalized attestation verified ·{" "}
                  {verifiedAttestation.recordId}
                  {" v"}
                  {verifiedAttestation.recordVersion}
                </strong>
              ) : null}
            </div>
          ) : null}

          {attestError !== null ? (
            <p
              className="mission-error"
              role="alert"
            >
              {attestError}
            </p>
          ) : null}
        </article>

        <article className="evidence-panel evidence-panel-register">
          <div className="evidence-panel-title">
            <FileCheck2
              size={20}
              aria-hidden="true"
            />
            <div>
              <p>PRINCIPAL / REGISTER</p>
              <h3>
                Bind an existing attestation into the mission manifest.
              </h3>
            </div>
          </div>

          <div className="evidence-form-grid">
            <label>
              <span>Mission ID</span>
              <input
                value={registerMissionId}
                onChange={(event) => {
                  setRegisterMissionId(
                    event.target.value,
                  );
                  resetRegistration();
                }}
                placeholder="Mission ID"
                maxLength={512}
              />
            </label>

            <label>
              <span>Evidence ID</span>
              <input
                value={evidenceId}
                onChange={(event) => {
                  setEvidenceId(
                    event.target.value,
                  );
                  resetRegistration();
                }}
                placeholder="evidence-primary"
                maxLength={512}
              />
            </label>

            <label>
              <span>Authority ID</span>
              <input
                value={registerAuthorityId}
                onChange={(event) => {
                  setRegisterAuthorityId(
                    event.target.value,
                  );
                  resetRegistration();
                }}
                placeholder="authority-id"
                maxLength={64}
              />
            </label>

            <label>
              <span>Record ID</span>
              <input
                value={registerRecordId}
                onChange={(event) => {
                  setRegisterRecordId(
                    event.target.value,
                  );
                  resetRegistration();
                }}
                placeholder="stable-record-id"
                maxLength={512}
              />
            </label>

            <label>
              <span>Record version</span>
              <input
                value={registerRecordVersion}
                onChange={(event) => {
                  setRegisterRecordVersion(
                    event.target.value,
                  );
                  resetRegistration();
                }}
                inputMode="numeric"
              />
            </label>
          </div>

          <div className="evidence-rule-note">
            Registration is principal-only, PREPARING-only, and deadline
            bounded. The selected attestation must already exist in finalized
            state and match this mission, mission version, authority identity,
            record identity, and record version.
          </div>

          {registerQuote === null ? (
            <button
              className="mission-primary-button"
              type="button"
              disabled={
                registerBusy
                || registerMissionId.length === 0
                || evidenceId.length === 0
                || registerAuthorityId.length === 0
                || registerRecordId.length === 0
              }
              onClick={reviewRegistration}
            >
              {registerBusy ? (
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
              Preflight registration
            </button>
          ) : (
            <div className="evidence-review">
              <dl>
                <div>
                  <dt>Mission state</dt>
                  <dd>
                    {registerQuote.mission.state}
                  </dd>
                </div>
                <div>
                  <dt>Mission version</dt>
                  <dd>
                    {registerQuote.mission.version}
                  </dd>
                </div>
                <div>
                  <dt>Existing evidence</dt>
                  <dd>
                    {registerQuote.existingEvidence.length}
                    {" / 16"}
                  </dd>
                </div>
                <div>
                  <dt>Issuer</dt>
                  <dd>
                    {registerQuote.attestation.issuerAddress}
                  </dd>
                </div>
                <div>
                  <dt>Attestation URL</dt>
                  <dd>
                    {registerQuote.attestation.url}
                  </dd>
                </div>
                <div>
                  <dt>Quoted fee</dt>
                  <dd>
                    {formatGenAmount(
                      registerQuote.feeValue,
                    )} GEN
                  </dd>
                </div>
              </dl>

              <button
                className="mission-primary-button"
                type="button"
                disabled={
                  registerBusy
                  || registerProgress !== null
                }
                onClick={signRegistration}
              >
                {registerBusy ? (
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
                Sign &amp; register evidence
              </button>
            </div>
          )}

          {registerProgress !== null ? (
            <div className="evidence-progress">
              <span>
                {registerProgress.phase}
              </span>
              <code>
                {registerProgress.txId}
              </code>
              {verifiedEvidence !== null ? (
                <strong>
                  Registered evidence verified ·{" "}
                  {verifiedEvidence.evidenceId}
                  {" · "}
                  {verifiedEvidence.authorityId}
                </strong>
              ) : null}
            </div>
          ) : null}

          {registerError !== null ? (
            <p
              className="mission-error"
              role="alert"
            >
              {registerError}
            </p>
          ) : null}
        </article>
      </div>
    </section>
  );
}
