"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  CircleCheck,
  ExternalLink,
  ShieldCheck,
  Unplug,
  WalletCards,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";
import {
  CommitMark,
} from "@/components/brand/commit-mark";
import {
  CreateMissionFlow,
} from "@/components/application/create-mission-flow";
import {
  FundMissionFlow,
} from "@/components/application/fund-mission-flow";
import {
  PrepareMissionFlow,
} from "@/components/application/prepare-mission-flow";
import {
  EvidenceMissionFlow,
} from "@/components/application/evidence-mission-flow";
import {
  SealMissionFlow,
} from "@/components/application/seal-mission-flow";
import {
  ResolutionMissionFlow,
} from "@/components/application/resolution-mission-flow";
import {
  ClaimMissionFlow,
} from "@/components/application/claim-mission-flow";
import {
  CaseRoom,
} from "@/components/justice/case-room";
import {
  preflightCommitWallet,
  STUDIO_NEXT_CHAIN_ID,
  type ConnectedCommitWallet,
  type WalletPreflight,
} from "@/lib/genlayer-browser";
import {
  connectCommitWallet,
  walletConnectionErrorMessage,
} from "@/lib/commit-wallet-connection";
import {
  CURRENT_DEPLOYMENT_ANCHOR,
} from "@/lib/deployment-anchor";

function shorten(
  value: string,
): string {
  return `${value.slice(0, 7)}…${value.slice(-5)}`;
}

export function ApplicationShell() {
  const [
    wallet,
    setWallet,
  ] = useState<ConnectedCommitWallet | null>(
    null,
  );
  const [
    connecting,
    setConnecting,
  ] = useState(false);
  const [
    walletError,
    setWalletError,
  ] = useState<string | null>(
    null,
  );

  const [
    walletPreflight,
    setWalletPreflight,
  ] = useState<WalletPreflight | null>(
    null,
  );
  const [
    lastMissionId,
    setLastMissionId,
  ] = useState("");

  useEffect(() => {
    if (wallet === null) {
      return;
    }

    const invalidate = () => {
      setWallet(
        null,
      );
      setWalletPreflight(
        null,
      );
      setLastMissionId(
        "",
      );
      setWalletError(
        "Wallet account or network changed. Reconnect before signing another COMMIT transaction.",
      );
    };

    wallet.provider.on?.(
      "accountsChanged",
      invalidate,
    );
    wallet.provider.on?.(
      "chainChanged",
      invalidate,
    );

    return () => {
      wallet.provider.removeListener?.(
        "accountsChanged",
        invalidate,
      );
      wallet.provider.removeListener?.(
        "chainChanged",
        invalidate,
      );
    };
  }, [wallet]);

  async function connectWallet() {
    setConnecting(
      true,
    );
    setWalletError(
      null,
    );

    try {
      const connected =
        await connectCommitWallet();

      const preflight =
        await preflightCommitWallet(
          connected,
        );

      setWallet(
        connected,
      );
      setWalletPreflight(
        preflight,
      );
    } catch (error: unknown) {
      setWallet(
        null,
      );
      setWalletPreflight(
        null,
      );
      setWalletError(
        walletConnectionErrorMessage(
          error,
        ),
      );
    } finally {
      setConnecting(
        false,
      );
    }
  }

  return (
    <main className="commit-app-shell">
      <header className="commit-app-header">
        <Link className="commit-brand" href="/">
          <CommitMark className="commit-brand-mark" />
          <span className="commit-brand-word">
            COMMIT
            <small>Application</small>
          </span>
        </Link>

        <nav className="commit-app-nav" aria-label="Application">
          <a href="#case-room">Case room</a>
          <a href="#create">Create</a>
          <a href="#fund">Fund</a>
          <a href="#prepare">Prepare</a>
          <a href="#evidence">Evidence</a>
          <a href="#seal">Seal</a>
          <a href="#resolve">Resolve</a>
          <a href="#claim">Claim</a>
          <a href="#verify">Verify</a>
        </nav>

        {wallet === null ? (
          <button
            className="wallet-button"
            type="button"
            onClick={connectWallet}
            disabled={connecting}
          >
            <WalletCards
              size={16}
              aria-hidden="true"
            />
            {connecting
              ? "Connecting…"
              : "Connect wallet"}
          </button>
        ) : (
          <button
            className="wallet-button wallet-connected"
            type="button"
            onClick={() => {
              setWallet(
                null,
              );
              setWalletPreflight(
                null,
              );
              setLastMissionId(
                "",
              );
              setWalletError(
                null,
              );
            }}
            title="Disconnect this local COMMIT session"
          >
            <CircleCheck
              size={16}
              aria-hidden="true"
            />
            {shorten(wallet.address)}
          </button>
        )}
      </header>

      <section className="commit-app-hero">
        <div>
          <p className="commit-app-kicker">
            LIVE APPLICATION / STUDIO NEXT
          </p>
          <h1 className="commit-display">
            RESOLVE.
            <span>WITH PROOF.</span>
            <small>ENFORCE WITH FINALITY.</small>
          </h1>
        </div>
        <div className="commit-app-hero-copy">
          <p>
            COMMIT is an Onchain Justice protocol for agent commerce. Freeze
            the agreement, hold escrow, bind authenticated evidence, let
            GenLayer adjudicate the outcome, and enforce the result only after
            finality.
          </p>
          <div className="commit-app-anchor">
            <span>
              Chain {STUDIO_NEXT_CHAIN_ID}
            </span>
            <span>
              {shorten(
                CURRENT_DEPLOYMENT_ANCHOR.contractAddress,
              )}
            </span>
            <span>
              Contract unchanged
            </span>
          </div>
        </div>
      </section>

      <section className="commit-app-status">
        <article>
          <ShieldCheck
            size={20}
            aria-hidden="true"
          />
          <span>Write target</span>
          <strong>Existing coordinator</strong>
          <small>No redeployment required</small>
        </article>
        <article>
          <WalletCards
            size={20}
            aria-hidden="true"
          />
          <span>Signer</span>
          <strong>
            {wallet === null
              ? "Not connected"
              : shorten(wallet.address)}
          </strong>
          <small>
            {walletPreflight === null
              ? "Wallet / Studio Next 61997"
              : `${walletPreflight.balanceGen} GEN available`}
          </small>
        </article>
        <article>
          <Activity
            size={20}
            aria-hidden="true"
          />
          <span>Lifecycle</span>
          <strong>Quote → sign → finality</strong>
          <small>Provisional verdicts stay visibly appealable</small>
        </article>
      </section>

      {walletError !== null ? (
        <div className="commit-wallet-alert" role="alert">
          <Unplug
            size={18}
            aria-hidden="true"
          />
          <div>
            <strong>Wallet action required</strong>
            <p>{walletError}</p>
          </div>
        </div>
      ) : null}

      <section className="justice-case-section">
        {wallet === null ? (
          <div className="justice-case-gate">
            <div>
              <p>ONCHAIN JUSTICE / CASE ROOM</p>
              <h2 className="commit-display">
                AGREEMENT.
                <span>EVIDENCE.</span>
                FINALITY.
              </h2>
              <p>
                Connect a wallet to inspect a live agreement, its authenticated
                evidence, provisional verdict, native appeal window, and
                finalized settlement consequence.
              </p>
            </div>
            <button
              className="commit-action commit-action-hot"
              type="button"
              onClick={connectWallet}
              disabled={connecting}
            >
              <WalletCards size={18} aria-hidden="true" />
              {connecting ? "Connecting wallet…" : "Connect to open a case"}
            </button>
          </div>
        ) : (
          <CaseRoom
            key={`${lastMissionId || "case-room"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="create" className="commit-app-create">
        {wallet === null ? (
          <div className="wallet-gate">
            <div className="wallet-gate-mark">
              <CommitMark />
            </div>
            <p>01 / CONNECT</p>
            <h2 className="commit-display">
              YOUR WALLET IS
              <span>THE PRINCIPAL.</span>
            </h2>
            <p className="wallet-gate-copy">
              COMMIT never asks for a private key. Connect an injected
              MetaMask-compatible wallet, connect to GenLayer Studio Next
              (chain 61997), and review the exact fee quote before the wallet
              is asked to sign anything.
            </p>
            <button
              className="commit-action commit-action-hot"
              type="button"
              onClick={connectWallet}
              disabled={connecting}
            >
              <WalletCards
                size={18}
                aria-hidden="true"
              />
              {connecting
                ? "Connecting wallet…"
                : "Connect wallet to create"}
            </button>
          </div>
        ) : (
          <CreateMissionFlow
            wallet={wallet}
            onMissionFinalized={(missionId) => {
              setLastMissionId(
                missionId,
              );
            }}
          />
        )}
      </section>

      <section id="fund" className="commit-app-fund">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>02 / FUND</p>
            <h2 className="commit-display">
              CONNECT BEFORE
              <span>DEPOSITING VALUE.</span>
            </h2>
            <p>
              Funding is principal-only and payable. COMMIT will not expose
              the signing action until the wallet, mission state, deadline,
              and remaining budget are verified.
            </p>
          </div>
        ) : (
          <FundMissionFlow
            key={`${lastMissionId || "manual-funding"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="prepare" className="commit-app-prepare">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>03 / PREPARE</p>
            <h2 className="commit-display">
              AUTHORIZE.
              <span>PREPARE EFFECTS.</span>
            </h2>
            <p>
              Supplier authorization and effect preparation are consequential
              writes. Connect the mission wallet before COMMIT exposes either
              signing path.
            </p>
          </div>
        ) : (
          <PrepareMissionFlow
            key={`${lastMissionId || "manual-prepare"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="evidence" className="commit-app-evidence">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>04 / EVIDENCE</p>
            <h2 className="commit-display">
              ATTEST.
              <span>REGISTER.</span>
            </h2>
            <p>
              Evidence is role-bound. Authority issuers attest immutable,
              versioned records; mission principals register matching
              attestations into the mission before sealing.
            </p>
          </div>
        ) : (
          <EvidenceMissionFlow
            key={`${lastMissionId || "manual-evidence"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="seal" className="commit-app-seal">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>05 / SEAL</p>
            <h2 className="commit-display">
              DERIVE.
              <span>LOCK ROOTS.</span>
            </h2>
            <p>
              Sealing is principal-only. COMMIT derives both roots from
              finalized coordinator state, verifies evidence corroboration and
              the effect graph, then presents the exact write for review.
            </p>
          </div>
        ) : (
          <SealMissionFlow
            key={`${lastMissionId || "manual-seal"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="resolve" className="commit-app-resolution">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>06 / RESOLVE</p>
            <h2 className="commit-display">
              EVALUATE.
              <span>RECOVER.</span>
            </h2>
            <p>
              Evaluation and deadline recovery are permissionless. Evidence
              repair remains principal-only and exact-record-bound. Allocation
              is reported only from finalized coordinator state.
            </p>
          </div>
        ) : (
          <ResolutionMissionFlow
            key={`${lastMissionId || "manual-resolution"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="claim" className="commit-app-claim">
        {wallet === null ? (
          <div className="fund-wallet-gate">
            <p>07 / CLAIM</p>
            <h2 className="commit-display">
              CLAIM.
              <span>VERIFY RECEIPT.</span>
            </h2>
            <p>
              Terminal entitlements are beneficiary pull payments. COMMIT
              verifies mission-specific claimable state before signing and the
              exact finalized DISPATCHED withdrawal record afterward.
            </p>
          </div>
        ) : (
          <ClaimMissionFlow
            key={`${lastMissionId || "manual-claim"}:${wallet.address}`}
            wallet={wallet}
            initialMissionId={lastMissionId}
          />
        )}
      </section>

      <section id="verify" className="commit-app-next">
        <div>
          <p>COMPLETE PROTOCOL LIFECYCLE</p>
          <h2 className="commit-display">
            CREATE.<span>RESOLVE.</span>CLAIM.
          </h2>
        </div>
        <div className="commit-app-next-copy">
          <p>
            The complete case lifecycle is represented against the frozen
            coordinator: agreement, escrow, evidence, verdict, native appeal,
            finality, enforcement, claim, and independent verification. The
            Case Room makes each protocol boundary legible without inventing
            contract states.
          </p>
          <Link href="/verify">
            Open advanced verification
            <ExternalLink
              size={15}
              aria-hidden="true"
            />
          </Link>
        </div>
      </section>

      <footer className="commit-app-footer">
        <span>COMMIT / ONCHAIN JUSTICE</span>
        <Link href="/">
          Back to product
          <ArrowRight
            size={14}
            aria-hidden="true"
          />
        </Link>
      </footer>
    </main>
  );
}
