import {
  abi,
  createClient,
  decodeInputData,
} from "genlayer-js";
import type {
  GenLayerTransaction,
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
  | "FINALIZED"
  | "FINALIZED_ERROR"
  | "FINALIZED_UNKNOWN";

export type AppealTransactionBinding = {
  coordinator: `0x${string}`;
  missionId: string;
};

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
  transactionTarget: `0x${string}`;
  transactionFunctionName: string;
  transactionMissionId: string;
  executionResultName: string | null;
  executionSucceeded: boolean | null;
};

type AppealCapableClient = Pick<
  ConnectedCommitWallet["client"],
  | "advanced"
  | "canAppeal"
  | "getAppealCharge"
  | "appealTransaction"
  | "getTransaction"
>;

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function valueAt(source: unknown, key: string): unknown {
  if (source instanceof Map) {
    return source.get(key);
  }

  return isRecord(source) ? source[key] : undefined;
}

function validAddress(value: unknown): value is `0x${string}` {
  return typeof value === "string"
    && /^0x[0-9a-fA-F]{40}$/.test(value);
}

function decodeTransactionCallData(
  transaction: GenLayerTransaction,
): unknown {
  const decoded = transaction.txDataDecoded;

  if (
    isRecord(decoded)
    && valueAt(decoded, "callData") !== undefined
  ) {
    return valueAt(decoded, "callData");
  }

  const target = transaction.to_address ?? transaction.recipient;

  if (transaction.txData !== undefined && validAddress(target)) {
    const decodedInput = decodeInputData(
      transaction.txData,
      target,
    );

    if (
      isRecord(decodedInput)
      && valueAt(decodedInput, "callData") !== undefined
    ) {
      return valueAt(decodedInput, "callData");
    }
  }

  const transactionData = transaction.data;
  const calldata = isRecord(transactionData)
    ? transactionData.calldata
    : undefined;
  const raw = isRecord(calldata) ? calldata.raw : undefined;

  if (raw instanceof Uint8Array) {
    return abi.calldata.decode(raw);
  }

  if (
    Array.isArray(raw)
    && raw.every((item) => Number.isInteger(item) && item >= 0 && item <= 255)
  ) {
    return abi.calldata.decode(Uint8Array.from(raw));
  }

  throw new Error(
    "GenLayer did not expose decodable calldata for the evaluation transaction.",
  );
}

type AppealTransactionMetadata = {
  target: `0x${string}`;
  functionName: string;
  missionId: string;
  executionResultName: string | null;
  executionSucceeded: boolean | null;
};

function readTransactionMetadata(
  transaction: GenLayerTransaction,
): AppealTransactionMetadata {
  const target = transaction.to_address ?? transaction.recipient;

  if (!validAddress(target)) {
    throw new Error(
      "The evaluation transaction has no valid contract target.",
    );
  }

  const callData = decodeTransactionCallData(transaction);
  const functionName = valueAt(callData, "")
    ?? valueAt(callData, "method");
  const args = valueAt(callData, "args");
  const missionId = Array.isArray(args) ? args[0] : undefined;

  if (typeof functionName !== "string") {
    throw new Error(
      "The evaluation transaction calldata does not identify a method.",
    );
  }

  if (typeof missionId !== "string") {
    throw new Error(
      "The evaluation transaction calldata does not contain a mission ID.",
    );
  }

  const executionResultName = typeof transaction.txExecutionResultName === "string"
    ? transaction.txExecutionResultName
    : null;

  return {
    target,
    functionName,
    missionId,
    executionResultName,
    executionSucceeded: executionResultName === null
      ? null
      : executionResultName === "FINISHED_WITH_RETURN",
  };
}

function assertAppealTransactionBinding(
  metadata: AppealTransactionMetadata,
  binding: AppealTransactionBinding,
): void {
  if (metadata.target.toLowerCase() !== binding.coordinator.toLowerCase()) {
    throw new Error(
      "The supplied transaction targets a different contract than the certified COMMIT coordinator.",
    );
  }

  if (metadata.missionId !== binding.missionId) {
    throw new Error(
      "The supplied evaluation transaction belongs to a different mission.",
    );
  }
}

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
  > & Pick<AppealLifecycleSnapshot, "executionSucceeded">,
): AppealLifecyclePhase {
  if (lifecycle.storedStatus === "Finalized") {
    if (lifecycle.executionSucceeded === true) {
      return "FINALIZED";
    }

    return lifecycle.executionSucceeded === false
      ? "FINALIZED_ERROR"
      : "FINALIZED_UNKNOWN";
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
  binding?: AppealTransactionBinding,
): Promise<AppealLifecycleSnapshot> {
  assertTransactionHash(txId);

  const [lifecycle, transaction] = await Promise.all([
    client.advanced.getTransactionLifecycle({
      hash: txId,
    }),
    client.getTransaction({
      hash: txId,
    }),
  ]);
  const transactionMetadata = readTransactionMetadata(transaction);

  if (transactionMetadata.functionName !== "evaluate_mission") {
    throw new Error(
      "The supplied transaction is not a coordinator evaluate_mission call.",
    );
  }

  if (binding !== undefined) {
    assertAppealTransactionBinding(transactionMetadata, binding);
  }

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
    transactionTarget: transactionMetadata.target,
    transactionFunctionName: transactionMetadata.functionName,
    transactionMissionId: transactionMetadata.missionId,
    executionResultName: transactionMetadata.executionResultName,
    executionSucceeded: transactionMetadata.executionSucceeded,
    phase: classifyAppealLifecycle({
      storedStatus: lifecycle.storedStatus,
      decisionActive: lifecycle.decisionActive,
      canAppeal,
      executionSucceeded: transactionMetadata.executionSucceeded,
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
  binding?: AppealTransactionBinding,
): Promise<TransactionHash> {
  assertTransactionHash(txId);

  const current = await readAppealLifecycle(
    wallet.client,
    txId,
    binding,
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
    case "FINALIZED_ERROR":
      return "Finalized — execution failed";
    case "FINALIZED_UNKNOWN":
      return "Finalized — execution result unavailable";
  }
}

export function appealChargeLabel(
  value: bigint | null,
): string {
  return value === null
    ? "Not available"
    : `${formatGenAmount(value)} GEN`;
}
