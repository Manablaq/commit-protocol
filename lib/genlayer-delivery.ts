import {
  ExecutionResult,
  TransactionStatus,
  type GenLayerTransaction,
  type TransactionHash,
} from "genlayer-js/types";
import type {
  ConnectedCommitWallet,
} from "@/lib/genlayer-browser";

/**
 * This is an operator-side observation of the child transaction created by a
 * native-value message. It is deliberately not contract state and it never
 * authorizes a retry.
 */
export type ExternalDeliveryPhase =
  | "PENDING"
  | "DELIVERED"
  | "FAILED"
  | "UNVERIFIED";

export type ExternalDeliveryChild = {
  transactionId: TransactionHash;
  recipient: `0x${string}` | null;
  amount: bigint | null;
  bindingVerified: boolean;
  statusName: string | null;
  executionResultName: string | null;
  finalized: boolean;
  successful: boolean | null;
};

export type ExternalDeliveryObservation = {
  parentTransactionId: TransactionHash;
  childTransactionIds: TransactionHash[];
  phase: ExternalDeliveryPhase;
  child: ExternalDeliveryChild | null;
  reason: string;
  observedAt: number;
};

type DeliveryReadClient = Pick<
  ConnectedCommitWallet["client"],
  "getTriggeredTransactionIds" | "getTransaction"
>;

const CLAIM_TX_STORAGE_PREFIX = "commit:claim-tx:";

export type ExternalDeliveryExpectation = {
  recipient: `0x${string}`;
  amount: bigint;
};

export type PersistedClaimTransaction = {
  missionId: string;
  beneficiary: `0x${string}`;
  transactionId: TransactionHash;
  amount: bigint;
};

function isTransactionHash(
  value: string,
): value is TransactionHash {
  return /^0x[0-9a-fA-F]{64}$/.test(value);
}

function assertTransactionHash(
  value: string,
): asserts value is TransactionHash {
  if (!isTransactionHash(value)) {
    throw new Error("GenLayer returned an invalid transaction hash.");
  }
}

function executionResultName(
  transaction: GenLayerTransaction,
): string | null {
  return typeof transaction.txExecutionResultName === "string"
    ? transaction.txExecutionResultName
    : null;
}

function statusName(
  transaction: GenLayerTransaction,
): string | null {
  return typeof transaction.statusName === "string"
    ? transaction.statusName
    : null;
}

function transactionRecipient(
  transaction: GenLayerTransaction,
): `0x${string}` | null {
  const candidate = transaction.to_address ?? transaction.recipient;

  return typeof candidate === "string"
    && /^0x[0-9a-fA-F]{40}$/.test(candidate)
    ? candidate as `0x${string}`
    : null;
}

function transactionAmount(
  transaction: GenLayerTransaction,
): bigint | null {
  const value = transaction.value;

  if (typeof value === "bigint") {
    return value >= BigInt(0) ? value : null;
  }

  if (
    typeof value === "number"
    && Number.isSafeInteger(value)
    && value >= 0
  ) {
    return BigInt(value);
  }

  if (typeof value === "string" && /^[0-9]+$/.test(value)) {
    return BigInt(value);
  }

  return null;
}

function childObservation(
  transactionId: TransactionHash,
  transaction: GenLayerTransaction,
  expected: ExternalDeliveryExpectation,
): ExternalDeliveryChild {
  const status = statusName(transaction);
  const result = executionResultName(transaction);
  const finalized = status === TransactionStatus.FINALIZED;
  const recipient = transactionRecipient(transaction);
  const amount = transactionAmount(transaction);
  const bindingVerified = recipient !== null
    && amount !== null
    && recipient.toLowerCase() === expected.recipient.toLowerCase()
    && amount === expected.amount;

  return {
    transactionId,
    recipient,
    amount,
    bindingVerified,
    statusName: status,
    executionResultName: result,
    finalized,
    successful: finalized && bindingVerified
      ? result === ExecutionResult.FINISHED_WITH_RETURN
        ? true
        : result === ExecutionResult.FINISHED_WITH_ERROR
          ? false
          : null
      : null,
  };
}

function observation(
  parentTransactionId: TransactionHash,
  childTransactionIds: TransactionHash[],
  phase: ExternalDeliveryPhase,
  child: ExternalDeliveryChild | null,
  reason: string,
): ExternalDeliveryObservation {
  return {
    parentTransactionId,
    childTransactionIds,
    phase,
    child,
    reason,
    observedAt: Date.now(),
  };
}

export function unverifiedExternalDelivery(
  parentTransactionId: TransactionHash,
  reason: string,
): ExternalDeliveryObservation {
  return observation(
    parentTransactionId,
    [],
    "UNVERIFIED",
    null,
    reason,
  );
}

/**
 * Observe the exact child transaction(s) emitted by a parent claim.
 *
 * Strict rules:
 * - no child ID is not treated as success;
 * - more than one child ID is ambiguous for the one-transfer claim path;
 * - only FINALIZED + FINISHED_WITH_RETURN is delivered;
 * - only FINALIZED + FINISHED_WITH_ERROR is failed;
 * - every other state is pending or unverified;
 * - this function has no write or retry capability.
 */
export async function observeExternalDelivery(
  client: DeliveryReadClient,
  parentTransactionId: string,
  expected: ExternalDeliveryExpectation,
): Promise<ExternalDeliveryObservation> {
  assertTransactionHash(parentTransactionId);

  let childTransactionIds: TransactionHash[];

  try {
    childTransactionIds = await client.getTriggeredTransactionIds({
      hash: parentTransactionId,
    });
  } catch {
    return observation(
      parentTransactionId,
      [],
      "UNVERIFIED",
      null,
      "The Studio Next RPC did not return triggered child transaction IDs. No delivery outcome is claimed.",
    );
  }

  if (childTransactionIds.length === 0) {
    return observation(
      parentTransactionId,
      [],
      "UNVERIFIED",
      null,
      "No triggered child transaction ID is exposed yet. This is not proof of delivery or non-delivery.",
    );
  }

  if (!childTransactionIds.every(isTransactionHash)) {
    return observation(
      parentTransactionId,
      [],
      "UNVERIFIED",
      null,
      "The Studio Next RPC returned a malformed child transaction ID. No delivery outcome is claimed.",
    );
  }

  if (childTransactionIds.length !== 1) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      null,
      "The claim produced an unexpected number of child transactions. Delivery is ambiguous and no retry is authorized.",
    );
  }

  const [childTransactionId] = childTransactionIds;
  let transaction: GenLayerTransaction;

  try {
    transaction = await client.getTransaction({
      hash: childTransactionId,
    });
  } catch {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      null,
      "The Studio Next RPC did not return the exact child transaction. No delivery outcome is claimed.",
    );
  }
  const child = childObservation(
    childTransactionId,
    transaction,
    expected,
  );

  if (!child.bindingVerified) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      child,
      "The child transaction does not prove the expected recipient and exact GEN amount. No delivery outcome is claimed.",
    );
  }

  if (child.successful === true) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "DELIVERED",
      child,
      "The exact triggered child transaction finalized successfully.",
    );
  }

  if (child.successful === false) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "FAILED",
      child,
      "The exact triggered child transaction finalized with an execution error. COMMIT does not automatically retry or restore the entitlement.",
    );
  }

  if (child.finalized) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      child,
      "The child transaction finalized without a recognized successful or failed execution result. No delivery outcome is claimed.",
    );
  }

  return observation(
    parentTransactionId,
    childTransactionIds,
    "PENDING",
    child,
    "The exact triggered child transaction has not finalized. Do not infer failure from elapsed time and do not retry.",
  );
}

export function claimTransactionStorageKey(
  missionId: string,
  beneficiary: `0x${string}`,
): string {
  return `${CLAIM_TX_STORAGE_PREFIX}${encodeURIComponent(missionId)}:${beneficiary.toLowerCase()}`;
}

export function readPersistedClaimTransaction(
  missionId: string,
  beneficiary: `0x${string}`,
): PersistedClaimTransaction | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const stored = window.localStorage.getItem(
      claimTransactionStorageKey(missionId, beneficiary),
    );

    if (stored === null) {
      return null;
    }

    const candidate: unknown = JSON.parse(stored);

    if (
      typeof candidate !== "object"
      || candidate === null
      || Array.isArray(candidate)
    ) {
      return null;
    }

    const record = candidate as Record<string, unknown>;

    if (
      typeof record.missionId !== "string"
      || typeof record.beneficiary !== "string"
      || !/^0x[0-9a-fA-F]{40}$/.test(record.beneficiary)
      || record.missionId !== missionId
      || record.beneficiary.toLowerCase() !== beneficiary.toLowerCase()
      || typeof record.transactionId !== "string"
      || !isTransactionHash(record.transactionId)
      || typeof record.amount !== "string"
      || !/^[1-9][0-9]*$/.test(record.amount)
    ) {
      return null;
    }

    return {
      missionId: record.missionId,
      beneficiary: record.beneficiary as `0x${string}`,
      transactionId: record.transactionId,
      amount: BigInt(record.amount),
    };
  } catch {
    return null;
  }
}

export function persistClaimTransaction(
  missionId: string,
  beneficiary: `0x${string}`,
  transactionId: TransactionHash,
  amount: bigint,
): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(
      claimTransactionStorageKey(missionId, beneficiary),
      JSON.stringify({
        missionId,
        beneficiary: beneficiary.toLowerCase(),
        transactionId,
        amount: amount.toString(),
      }),
    );
  } catch {
    // Browser persistence is a convenience; delivery observation remains
    // available for the current session if storage is unavailable.
  }
}
