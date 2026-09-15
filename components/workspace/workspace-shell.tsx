"use client";

import {
  Activity,
  ArrowLeft,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  readHealth,
  readProtocolIndex,
  readTransaction,
  type ApiJson,
} from "@/lib/api";
import { CURRENT_DEPLOYMENT_ANCHOR } from "@/lib/deployment-anchor";
import { FinalityCard } from "@/components/workspace/finality-card";
import { IndexOverview } from "@/components/workspace/index-overview";
import { ProvenanceCard } from "@/components/workspace/provenance-card";
import { SemanticGraph } from "@/components/workspace/semantic-graph";
import { StateBoundary } from "@/components/workspace/state-boundary";
import { TransactionInspector } from "@/components/workspace/transaction-inspector";
import { CommitMark } from "@/components/brand/commit-mark";

function errorMessage(value: unknown): string {
  if (value instanceof Error) {
    return value.message;
  }

  return "The read-only protocol API returned an unknown error.";
}

function foundState(
  value: ApiJson | null,
): boolean {
  if (value === null) {
    return false;
  }

  const found = value.found;

  return typeof found === "boolean"
    ? found
    : true;
}

function boolValue(
  value: ApiJson | null,
  key: string,
): boolean {
  return value?.[key] === true;
}

function textValue(
  value: ApiJson | null,
  key: string,
): string {
  const candidate = value?.[key];

  return typeof candidate === "string"
    ? candidate
    : "Unknown";
}

export function WorkspaceShell() {
  const [health, setHealth] = useState<ApiJson | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [chainId, setChainId] = useState<string>(
    CURRENT_DEPLOYMENT_ANCHOR.chainId,
  );
  const [contractAddress, setContractAddress] = useState<string>(
    CURRENT_DEPLOYMENT_ANCHOR.contractAddress,
  );
  const [stateBasis, setStateBasis] = useState<string>(
    CURRENT_DEPLOYMENT_ANCHOR.stateBasis,
  );
  const [indexState, setIndexState] = useState<ApiJson | null>(null);
  const [indexLoading, setIndexLoading] = useState(false);
  const [indexError, setIndexError] = useState<string | null>(null);

  const [transactionId, setTransactionId] = useState<string>(
    CURRENT_DEPLOYMENT_ANCHOR.transactionId,
  );
  const [transactionState, setTransactionState] = useState<ApiJson | null>(null);
  const [transactionLoading, setTransactionLoading] = useState(false);
  const [transactionError, setTransactionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    readHealth()
      .then((value) => {
        if (active) {
          setHealth(value);
          setHealthError(null);
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setHealthError(errorMessage(error));
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const backendStatus = useMemo(() => {
    if (healthError !== null) {
      return "Unavailable";
    }

    if (health === null) {
      return "Checking";
    }

    return "Read surface online";
  }, [health, healthError]);

  async function submitIndex(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setIndexLoading(true);
    setIndexError(null);

    try {
      const value = await readProtocolIndex({
        chainId,
        contractAddress,
        stateBasis,
      });

      setIndexState(value);
    } catch (error: unknown) {
      setIndexState(null);
      setIndexError(errorMessage(error));
    } finally {
      setIndexLoading(false);
    }
  }

  async function submitTransaction(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setTransactionLoading(true);
    setTransactionError(null);

    try {
      const value = await readTransaction(
        transactionId,
      );

      setTransactionState(value);
    } catch (error: unknown) {
      setTransactionState(null);
      setTransactionError(errorMessage(error));
    } finally {
      setTransactionLoading(false);
    }
  }

  const transactionFinalized = boolValue(
    transactionState,
    "finalized",
  );

  const transactionStatus = textValue(
    transactionState,
    "status_name",
  );

  const indexBasis = textValue(
    indexState,
    "state_basis",
  );

  return (
    <main className="commit-app-shell commit-verify-shell">
      <header className="commit-app-header commit-verify-header">
        <Link
          className="commit-brand"
          href="/"
          aria-label="Back to COMMIT home"
        >
          <CommitMark className="commit-brand-mark" />
          <span className="commit-brand-word">
            COMMIT
            <small>Application</small>
          </span>
        </Link>

        <nav className="commit-app-nav" aria-label="Application">
          <Link href="/app#create">Create</Link>
          <Link href="/app#fund">Fund</Link>
          <Link href="/app#prepare">Prepare</Link>
          <Link href="/app#evidence">Evidence</Link>
          <Link href="/app#seal">Seal</Link>
          <Link href="/app#resolve">Resolve</Link>
          <Link href="/app#claim">Claim</Link>
          <Link href="/verify" aria-current="page">Verify</Link>
        </nav>

        <Link className="wallet-button commit-verify-back" href="/app#verify">
          <ArrowLeft size={16} aria-hidden="true" />
          Back to app
        </Link>
      </header>

      <section className="commit-app-hero commit-verify-hero">
        <div>
          <p className="commit-app-kicker">
            VERIFICATION CENTER / LIVE PROTOCOL
          </p>
          <h1 className="commit-display">
            Verify what the protocol <span>decided.</span>
          </h1>
        </div>

        <div className="commit-app-hero-copy">
          <p>
            Inspect the exact deployment, transaction consequence, evidence
            provenance, and finality state through COMMIT&apos;s certified
            read surface. Verification stays read-only and never becomes a
            second protocol authority.
          </p>

          <div className="commit-app-anchor">
            <span>Chain {CURRENT_DEPLOYMENT_ANCHOR.chainId}</span>
            <span>Read only</span>
            <span>{backendStatus}</span>
          </div>
        </div>
      </section>

      <section className="commit-app-status commit-verify-status">
        <article>
          <ShieldCheck size={20} aria-hidden="true" />
          <span>Deployment</span>
          <strong>Existing coordinator</strong>
          <small>{CURRENT_DEPLOYMENT_ANCHOR.networkLabel}</small>
        </article>

        <article>
          <Activity size={20} aria-hidden="true" />
          <span>Finality basis</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.stateBasis}</strong>
          <small>
            {CURRENT_DEPLOYMENT_ANCHOR.deploymentTransactionStatus}
            {" / "}
            {CURRENT_DEPLOYMENT_ANCHOR.deploymentExecutionResult}
          </small>
        </article>

        <article>
          <Search size={20} aria-hidden="true" />
          <span>Read surface</span>
          <strong>{backendStatus}</strong>
          <small>No wallet signature / no protocol write</small>
        </article>
      </section>

      <section className="deployment-anchor" aria-label="Current deployment anchor">
        <div>
          <span>Current source-matched deployment</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.networkLabel}</strong>
        </div>
        <div>
          <span>Chain</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.chainId}</strong>
        </div>
        <div className="deployment-anchor-wide">
          <span>Coordinator</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.contractAddress}</strong>
        </div>
        <div>
          <span>Deployment tx</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.deploymentTransactionStatus}</strong>
        </div>
        <div>
          <span>Execution</span>
          <strong>{CURRENT_DEPLOYMENT_ANCHOR.deploymentExecutionResult}</strong>
        </div>
      </section>

      <section className="query-deck">
        <form className="query-panel" onSubmit={submitIndex}>
          <div className="query-heading">
            <div>
              <span>01</span>
              <h2>Protocol index</h2>
            </div>
            <ShieldCheck size={18} aria-hidden="true" />
          </div>

          <label>
            <span>Chain ID</span>
            <input
              value={chainId}
              onChange={(event) => setChainId(event.target.value)}
              inputMode="numeric"
              placeholder="Enter exact chain ID"
              required
            />
          </label>

          <label>
            <span>Contract address</span>
            <input
              value={contractAddress}
              onChange={(event) => setContractAddress(event.target.value)}
              placeholder="Enter exact contract address"
              required
            />
          </label>

          <label>
            <span>State basis</span>
            <input
              value={stateBasis}
              onChange={(event) => setStateBasis(event.target.value)}
              placeholder="Enter backend-supported state basis"
              required
            />
          </label>

          <button className="query-button" type="submit" disabled={indexLoading}>
            {indexLoading ? (
              <RefreshCw className="spin" size={16} aria-hidden="true" />
            ) : (
              <Search size={16} aria-hidden="true" />
            )}
            Read index
          </button>
        </form>

        <form className="query-panel" onSubmit={submitTransaction}>
          <div className="query-heading">
            <div>
              <span>02</span>
              <h2>Transaction</h2>
            </div>
            <Activity size={18} aria-hidden="true" />
          </div>

          <label className="query-grow">
            <span>GenLayer transaction ID</span>
            <input
              value={transactionId}
              onChange={(event) => setTransactionId(event.target.value)}
              placeholder="Enter exact transaction ID"
              required
            />
          </label>

          <div className="query-note">
            <strong>No reconstructed chain truth.</strong>
            <p>
              The browser asks only the certified read surface for indexed
              transaction state.
            </p>
          </div>

          <button
            className="query-button"
            type="submit"
            disabled={transactionLoading}
          >
            {transactionLoading ? (
              <RefreshCw className="spin" size={16} aria-hidden="true" />
            ) : (
              <Search size={16} aria-hidden="true" />
            )}
            Read transaction
          </button>
        </form>
      </section>

      <section className="workspace-results">
        <div className="workspace-column">
          <div className="result-heading">
            <span>Indexed protocol state</span>
            <strong>Canonical browser authority: Step 7</strong>
          </div>

          <StateBoundary
            loading={indexLoading}
            error={indexError}
            found={foundState(indexState)}
            emptyLabel="No indexed protocol state matched the supplied identity."
          >
            {indexState === null ? (
              <div className="empty-instrument">
                <span className="instrument-crosshair" aria-hidden="true" />
                <strong>Awaiting an exact protocol identity</strong>
                <p>
                  Nothing is inferred before a certified API response exists.
                </p>
              </div>
            ) : (
              <>
                <IndexOverview value={indexState} />
                <div className="workspace-grid two">
                  <FinalityCard
                    finalized={
                      textValue(indexState, "state_status").toLowerCase() ===
                      "finalized"
                    }
                    stateBasis={indexBasis}
                  />
                  <ProvenanceCard value={indexState} />
                </div>
              </>
            )}
          </StateBoundary>
        </div>

        <div className="workspace-column">
          <div className="result-heading">
            <span>Transaction consequence</span>
            <strong>Accepted / finalized remain distinct</strong>
          </div>

          <StateBoundary
            loading={transactionLoading}
            error={transactionError}
            found={foundState(transactionState)}
            emptyLabel="No indexed transaction matched the supplied identity."
          >
            {transactionState === null ? (
              <div className="empty-instrument">
                <span className="instrument-crosshair" aria-hidden="true" />
                <strong>Awaiting a transaction identity</strong>
                <p>
                  Transaction state appears only after the read API returns it.
                </p>
              </div>
            ) : (
              <>
                <TransactionInspector value={transactionState} />
                <div className="workspace-grid two">
                  <FinalityCard
                    finalized={transactionFinalized}
                    statusName={transactionStatus}
                  />
                  <ProvenanceCard value={transactionState} />
                </div>
              </>
            )}
          </StateBoundary>
        </div>
      </section>

      <SemanticGraph />

      <footer className="commit-app-footer commit-verify-footer">
        <span>COMMIT / VERIFICATION CENTER</span>
        <Link href="/app#verify">
          Back to application
          <ArrowLeft size={14} aria-hidden="true" />
        </Link>
      </footer>
    </main>
  );
}
