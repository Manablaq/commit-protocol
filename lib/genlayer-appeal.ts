import {
  createClient,
} from "genlayer-js";
import type {
  TransactionHash,
} from "genlayer-js/types";
import {
  STUDIO_NEXT_CHAIN,
  formatGenAmount,
  type ConnectedCommitWallet,
} from "@/lib/genlayer-browser";

export type AppealLifecyclePhase =
  | "UNDER_REVIEW"
  | "PROVISIONAL"
  | "APPEAL_OPEN"
  | "APPEAL_IN_PROGRESS"
  | "FINALIZED";

export type AppealLifecycleSnapshot = {
  txId: TransactionHash;
  storedStatus: string;
  projectedStatus: string;
  resolutionAction: string;
  resolutionSource: string;
  decisionId: string | null;
  decisionActive: boolean;
  canAppeal: boolean;
  appealCharge: bigint | null;
  evaluatedAt: number;
  phase: AppealLifecyclePhase;
};

type AppealCapableClient = Pick<
  ConnectedCommitWallet["client"],
  "advanced" | "canAppeal" | "getAppealCharge" | "appealTransaction"
>;

function assertTransactionHash(
  value: string,
): asserts value is TransactionHash {
  if (!/^0x[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error(
      "GenLayer returned an invalid transaction hash.",
    );
  }
}

function isAppealInProgress(
  lifecycle: { storedStatus: string },
): boolean {
  return [
    "AppealCommitting",
    "AppealRevealing",
  ].includes(lifecycle.storedStatus);
}

export function classifyAppealLifecycle(
  lifecycle: Pick<
    AppealLifecycleSnapshot,
    "storedStatus" | "decisionActive" | "canAppeal"
  >,
): AppealLifecyclePhase {
  if (lifecycle.storedStatus === "Finalized") {
    return "FINALIZED";
  }

  if (isAppealInProgress(lifecycle)) {
    return "APPEAL_IN_PROGRESS";
  }

  if (lifecycle.decisionActive && lifecycle.canAppeal) {
    return "APPEAL_OPEN";
  }

  return lifecycle.decisionActive
    ? "PROVISIONAL"
    : "UNDER_REVIEW";
}

function appealEligibilityError(
  error: unknown,
): boolean {
  const message = error instanceof Error
    ? error.message
    : String(error);

  return /cannot appeal|can.?not appeal|appeal.*(closed|expired|inactive)|no active decision/i
    .test(message);
}

export function createStudioNextReadClient() {
  return createClient({
    chain: STUDIO_NEXT_CHAIN,
  });
}

export async function readAppealLifecycle(
  client: AppealCapableClient,
  txId: string,
): Promise<AppealLifecycleSnapshot> {
  assertTransactionHash(txId);

  const lifecycle = await client.advanced.getTransactionLifecycle({
    hash: txId,
  });

  let canAppeal = false;

  if (
    lifecycle.decisionActive
    && lifecycle.storedStatus !== "Finalized"
  ) {
    try {
      canAppeal = await client.canAppeal({
        txId,
      });
    } catch (error: unknown) {
      if (!appealEligibilityError(error)) {
        throw error;
      }
    }
  }

  const appealCharge = canAppeal
    ? await client.getAppealCharge({
        txId,
      })
    : null;

  return {
    txId,
    storedStatus: lifecycle.storedStatus,
    projectedStatus: lifecycle.projectedStatus,
    resolutionAction: lifecycle.resolutionAction,
    resolutionSource: lifecycle.resolutionSource,
    decisionId: lifecycle.decisionId,
    decisionActive: lifecycle.decisionActive,
    canAppeal,
    appealCharge,
    evaluatedAt: lifecycle.evaluatedAt,
    phase: classifyAppealLifecycle({
      storedStatus: lifecycle.storedStatus,
      decisionActive: lifecycle.decisionActive,
      canAppeal,
    }),
  };
}

export async function readStudioNextAppealLifecycle(
  txId: string,
): Promise<AppealLifecycleSnapshot> {
  return readAppealLifecycle(
    createStudioNextReadClient(),
    txId,
  );
}

export async function appealCommitTransaction(
  wallet: ConnectedCommitWallet,
  txId: string,
): Promise<TransactionHash> {
  assertTransactionHash(txId);

  const current = await readAppealLifecycle(
    wallet.client,
    txId,
  );

  if (!current.canAppeal) {
    throw new Error(
      "This decision is not currently appealable. Refresh the lifecycle before trying again.",
    );
  }

  // The public SDK reads the authoritative charge again immediately before
  // submission and binds the appeal to the active decision identity.
  await wallet.client.appealTransaction({
    txId,
  });

  return txId;
}

export function appealPhaseLabel(
  phase: AppealLifecyclePhase,
): string {
  switch (phase) {
    case "UNDER_REVIEW":
      return "Under validator review";
    case "PROVISIONAL":
      return "Provisional verdict";
    case "APPEAL_OPEN":
      return "Appeal window open";
    case "APPEAL_IN_PROGRESS":
      return "Appeal in progress";
    case "FINALIZED":
      return "Final verdict";
  }
}

export function appealChargeLabel(
  value: bigint | null,
): string {
  return value === null
    ? "Not available"
    : `${formatGenAmount(value)} GEN`;
}
