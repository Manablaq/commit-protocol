import {
  abi,
  decodeInputData,
} from "genlayer-js";
import {
  ExecutionResult,
  TransactionStatus,
  type GenLayerTransaction,
  type TransactionHash,
} from "genlayer-js/types";
import type {
  ConnectedCommitWallet,
} from "@/lib/genlayer-browser";
import {
  readBrowserStorage,
  writeBrowserStorage,
} from "@/lib/browser-storage";

/**
 * This is an operator-side observation of the child transaction created by a
 * native-value message. It is deliberately not contract state and it never
 * authorizes a retry.
 */
export type ExternalDeliveryPhase =
  | "PENDING"
  | "DELIVERED"
  | "FINALIZED_ERROR"
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

export type ExternalDeliveryOutboundMessage = {
  recipient: `0x${string}`;
  amount: bigint;
  data: string | null;
  onAcceptance: boolean | null;
};

export type ExternalDeliveryObservation = {
  parentTransactionId: TransactionHash;
  childTransactionIds: TransactionHash[];
  phase: ExternalDeliveryPhase;
  child: ExternalDeliveryChild | null;
  outboundMessage: ExternalDeliveryOutboundMessage | null;
  reason: string;
  observedAt: number;
};

type DeliveryReadClient = Pick<
  ConnectedCommitWallet["client"],
  "getTriggeredTransactionIds" | "getTransaction"
>;

const CLAIM_TX_STORAGE_PREFIX = "commit:claim-tx:";

export type ExternalDeliveryExpectation = {
  coordinator: `0x${string}`;
  missionId: string;
  recipient: `0x${string}`;
  /**
   * Optional convenience consistency check from the local claim quote. The
   * authoritative amount is always the finalized parent message itself.
   * A tampered local amount can only make the observation fail closed.
   */
  amount?: bigint;
};

export type PersistedClaimTransaction = {
  missionId: string;
  beneficiary: `0x${string}`;
  transactionId: TransactionHash;
  amount: bigint;
};

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function valueAt(source: unknown, key: string): unknown {
  if (source instanceof Map) {
    return source.get(key);
  }

  return isRecord(source) ? source[key] : undefined;
}

export function isTransactionHash(
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

function isAddress(value: unknown): value is `0x${string}` {
  return typeof value === "string"
    && /^0x[0-9a-fA-F]{40}$/.test(value);
}

function addressAt(
  source: unknown,
  key: string,
): `0x${string}` | null {
  const value = valueAt(source, key);
  return isAddress(value) ? value : null;
}

function bigintValue(value: unknown): bigint | null {
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

function transactionTarget(
  transaction: GenLayerTransaction,
): `0x${string}` | null {
  const candidate = transaction.to_address ?? transaction.recipient;
  return isAddress(candidate) ? candidate : null;
}

function transactionRecipient(
  transaction: GenLayerTransaction,
): `0x${string}` | null {
  const candidate = transaction.to_address ?? transaction.recipient;
  return isAddress(candidate) ? candidate : null;
}

function transactionAmount(
  transaction: GenLayerTransaction,
): bigint | null {
  return bigintValue(transaction.value);
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

  const target = transactionTarget(transaction);

  if (transaction.txData !== undefined && target !== null) {
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

  const calldata = valueAt(transaction.data, "calldata");
  const raw = valueAt(calldata, "raw");

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
    "GenLayer did not expose decodable calldata for the claim transaction.",
  );
}

function readClaimCall(
  transaction: GenLayerTransaction,
): { functionName: string; missionId: string } {
  const callData = decodeTransactionCallData(transaction);
  const functionName = valueAt(callData, "") ?? valueAt(callData, "method");
  const args = valueAt(callData, "args");
  const missionId = Array.isArray(args) ? args[0] : undefined;

  if (typeof functionName !== "string") {
    throw new Error(
      "The claim transaction calldata does not identify a method.",
    );
  }

  if (typeof missionId !== "string") {
    throw new Error(
      "The claim transaction calldata does not contain a mission ID.",
    );
  }

  return { functionName, missionId };
}

function readParentIdentity(
  transaction: GenLayerTransaction,
): { sender: `0x${string}`; origin: `0x${string}`; from: `0x${string}` } {
  const record = transaction as unknown as UnknownRecord;
  const sender = addressAt(record, "sender");
  const origin = addressAt(record, "origin_address");
  const from = addressAt(record, "from_address");

  if (sender === null || origin === null || from === null) {
    throw new Error(
      "The claim transaction did not expose sender, origin, and from_address together.",
    );
  }

  return { sender, origin, from };
}

function readOutboundMessage(
  transaction: GenLayerTransaction,
  expected: ExternalDeliveryExpectation,
): ExternalDeliveryOutboundMessage {
  const messages = transaction.messages;

  if (!Array.isArray(messages) || messages.length !== 1) {
    throw new Error(
      "The finalized claim did not expose exactly one native outbound message.",
    );
  }

  const message = messages[0];
  const recipient = addressAt(message, "recipient");
  const amount = bigintValue(valueAt(message, "value"));

  if (recipient === null || amount === null || amount <= BigInt(0)) {
    throw new Error(
      "The claim outbound message did not expose a valid recipient and positive GEN value.",
    );
  }

  if (recipient.toLowerCase() !== expected.recipient.toLowerCase()) {
    throw new Error(
      "The claim outbound message recipient does not match the beneficiary.",
    );
  }

  if (expected.amount !== undefined && amount !== expected.amount) {
    throw new Error(
      "The claim outbound message amount does not match the locally quoted amount.",
    );
  }

  const data = valueAt(message, "data");
  const onAcceptance = valueAt(message, "onAcceptance");

  return {
    recipient,
    amount,
    data: typeof data === "string" ? data : null,
    onAcceptance: typeof onAcceptance === "boolean" ? onAcceptance : null,
  };
}

function verifyParentClaim(
  transaction: GenLayerTransaction,
  expected: ExternalDeliveryExpectation,
): ExternalDeliveryOutboundMessage {
  const target = transactionTarget(transaction);

  if (
    target === null
    || target.toLowerCase() !== expected.coordinator.toLowerCase()
  ) {
    throw new Error(
      "The supplied parent transaction targets a different contract than the certified COMMIT coordinator.",
    );
  }

  const identity = readParentIdentity(transaction);
  if (
    identity.sender.toLowerCase() !== expected.recipient.toLowerCase()
    || identity.origin.toLowerCase() !== expected.recipient.toLowerCase()
    || identity.from.toLowerCase() !== expected.recipient.toLowerCase()
  ) {
    throw new Error(
      "The supplied parent transaction was not submitted by the connected beneficiary.",
    );
  }

  const call = readClaimCall(transaction);
  if (call.functionName !== "claim_mission") {
    throw new Error(
      "The supplied parent transaction is not a claim_mission call.",
    );
  }

  if (call.missionId !== expected.missionId) {
    throw new Error(
      "The supplied parent transaction belongs to a different mission.",
    );
  }

  return readOutboundMessage(transaction, expected);
}

function childObservation(
  transactionId: TransactionHash,
  transaction: GenLayerTransaction,
  expected: ExternalDeliveryExpectation,
  authoritativeAmount: bigint,
): ExternalDeliveryChild {
  const status = statusName(transaction);
  const result = executionResultName(transaction);
  const finalized = status === TransactionStatus.FINALIZED;
  const recipient = transactionRecipient(transaction);
  const amount = transactionAmount(transaction);
  const bindingVerified = recipient !== null
    && amount !== null
    && recipient.toLowerCase() === expected.recipient.toLowerCase()
    && amount === authoritativeAmount;

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
  outboundMessage: ExternalDeliveryOutboundMessage | null,
  reason: string,
): ExternalDeliveryObservation {
  return {
    parentTransactionId,
    childTransactionIds,
    phase,
    child,
    outboundMessage,
    reason,
    observedAt: Date.now(),
  };
}

export function unverifiedExternalDelivery(
  parentTransactionId: string,
  reason: string,
): ExternalDeliveryObservation {
  assertTransactionHash(parentTransactionId);

  return observation(
    parentTransactionId,
    [],
    "UNVERIFIED",
    null,
    null,
    reason,
  );
}

/**
 * Observe an exact native-value child only after independently verifying its
 * parent claim. The parent and outbound message are read from Studio Next;
 * browser storage is never treated as authority. No write or retry exists.
 */
export async function observeExternalDelivery(
  client: DeliveryReadClient,
  parentTransactionId: string,
  expected: ExternalDeliveryExpectation,
): Promise<ExternalDeliveryObservation> {
  assertTransactionHash(parentTransactionId);

  let parent: GenLayerTransaction;
  try {
    parent = await client.getTransaction({ hash: parentTransactionId });
  } catch {
    return unverifiedExternalDelivery(
      parentTransactionId,
      "The Studio Next RPC did not return the parent claim transaction. No delivery outcome is claimed.",
    );
  }

  const parentStatus = statusName(parent);
  if (parentStatus !== TransactionStatus.FINALIZED) {
    return observation(
      parentTransactionId,
      [],
      "PENDING",
      null,
      null,
      "The parent claim has not finalized. Do not infer delivery or failure from elapsed time.",
    );
  }

  if (executionResultName(parent) !== ExecutionResult.FINISHED_WITH_RETURN) {
    return unverifiedExternalDelivery(
      parentTransactionId,
      "The parent claim did not finalize successfully. No external delivery is claimed.",
    );
  }

  let outboundMessage: ExternalDeliveryOutboundMessage;
  try {
    outboundMessage = verifyParentClaim(parent, expected);
  } catch (caught: unknown) {
    return unverifiedExternalDelivery(
      parentTransactionId,
      caught instanceof Error
        ? `${caught.message} No delivery outcome is claimed.`
        : "The parent claim binding could not be verified. No delivery outcome is claimed.",
    );
  }

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
      outboundMessage,
      "The parent claim emitted the exact outbound GEN message, but Studio Next did not return triggered child IDs. Delivery is not proven.",
    );
  }

  if (childTransactionIds.length === 0) {
    return observation(
      parentTransactionId,
      [],
      "UNVERIFIED",
      null,
      outboundMessage,
      "The parent claim emitted the exact outbound GEN message, but no triggered child transaction ID is exposed. Delivery is not proven.",
    );
  }

  if (!childTransactionIds.every(isTransactionHash)) {
    return observation(
      parentTransactionId,
      [],
      "UNVERIFIED",
      null,
      outboundMessage,
      "The Studio Next RPC returned a malformed child transaction ID. No delivery outcome is claimed.",
    );
  }

  if (childTransactionIds.length !== 1) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      null,
      outboundMessage,
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
      outboundMessage,
      "The Studio Next RPC did not return the exact child transaction. No delivery outcome is claimed.",
    );
  }

  const child = childObservation(
    childTransactionId,
    transaction,
    expected,
    outboundMessage.amount,
  );

  if (!child.bindingVerified) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      child,
      outboundMessage,
      "The child transaction does not match the exact recipient and amount emitted by the verified parent message. No delivery outcome is claimed.",
    );
  }

  if (child.successful === true) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "DELIVERED",
      child,
      outboundMessage,
      "The verified parent emitted one exact outbound message and its exact child transaction finalized successfully.",
    );
  }

  if (child.successful === false) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "FINALIZED_ERROR",
      child,
      outboundMessage,
      "The exact child finalized with an execution error. This is not proof of terminal non-delivery and COMMIT does not automatically restore or retry the entitlement.",
    );
  }

  if (child.finalized) {
    return observation(
      parentTransactionId,
      childTransactionIds,
      "UNVERIFIED",
      child,
      outboundMessage,
      "The child transaction finalized without a recognized execution result. No delivery outcome is claimed.",
    );
  }

  return observation(
    parentTransactionId,
    childTransactionIds,
    "PENDING",
    child,
    outboundMessage,
    "The exact child transaction has not finalized. Do not infer failure from elapsed time and do not retry.",
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
  const stored = readBrowserStorage(
    claimTransactionStorageKey(missionId, beneficiary),
  );

  if (stored === null) {
    return null;
  }

  try {
    const candidate: unknown = JSON.parse(stored);

    if (
      !isRecord(candidate)
      || typeof candidate.missionId !== "string"
      || typeof candidate.beneficiary !== "string"
      || !/^0x[0-9a-fA-F]{40}$/.test(candidate.beneficiary)
      || candidate.missionId !== missionId
      || candidate.beneficiary.toLowerCase() !== beneficiary.toLowerCase()
      || typeof candidate.transactionId !== "string"
      || !isTransactionHash(candidate.transactionId)
      || typeof candidate.amount !== "string"
      || !/^[1-9][0-9]*$/.test(candidate.amount)
    ) {
      return null;
    }

    return {
      missionId: candidate.missionId,
      beneficiary: candidate.beneficiary as `0x${string}`,
      transactionId: candidate.transactionId,
      amount: BigInt(candidate.amount),
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
  writeBrowserStorage(
    claimTransactionStorageKey(missionId, beneficiary),
    JSON.stringify({
      missionId,
      beneficiary: beneficiary.toLowerCase(),
      transactionId,
      amount: amount.toString(),
    }),
  );
}
