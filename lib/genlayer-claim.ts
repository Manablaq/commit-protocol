import {
  TransactionHashVariant,
  type TransactionHash,
} from "genlayer-js/types";
import {
  CURRENT_DEPLOYMENT_ANCHOR,
} from "@/lib/deployment-anchor";
import {
  preflightCommitWallet,
  type ConnectedCommitWallet,
} from "@/lib/genlayer-browser";
import {
  readResolutionMission,
  type ResolutionMissionSnapshot,
} from "@/lib/genlayer-resolution";

const ZERO_BIGINT =
  BigInt(0);

export type ClaimMissionReceiptSnapshot = {
  missionId: string;
  state: string;
  decision: string;
  reasonCode: string;
  allocationApplied: boolean;
  refundBeneficiary: `0x${string}`;
  refundEntitlement: bigint;
  externalWithdrawalRecovery: boolean;
};

export type WithdrawalSnapshot = {
  withdrawalId: string;
  missionId: string;
  beneficiary: `0x${string}`;
  amount: bigint;
  status: string;
};

export type ClaimSnapshot = {
  mission: ResolutionMissionSnapshot;
  receipt: ClaimMissionReceiptSnapshot;
  beneficiary: `0x${string}`;
  missionClaimable: bigint;
  aggregateClaimable: bigint;
  withdrawalCount: number;
};

export type ClaimMissionQuote = Awaited<
  ReturnType<typeof quoteClaimMission>
>;

export type FinalizedClaimProof = {
  withdrawal: WithdrawalSnapshot;
  missionClaimableAfter: bigint;
  aggregateClaimableAfter: bigint;
  withdrawalCountAfter: number;
};

function valueRecord(
  value: unknown,
  label: string,
): Record<string, unknown> {
  if (
    typeof value !== "object"
    || value === null
    || Array.isArray(value)
  ) {
    throw new Error(
      `${label} returned an unexpected value.`,
    );
  }

  return value as Record<string, unknown>;
}

function valueString(
  value: unknown,
  label: string,
): string {
  if (typeof value !== "string") {
    throw new Error(
      `${label} returned an unexpected value.`,
    );
  }

  return value;
}

function valueBoolean(
  value: unknown,
  label: string,
): boolean {
  if (typeof value !== "boolean") {
    throw new Error(
      `${label} returned an unexpected value.`,
    );
  }

  return value;
}

function valueBigInt(
  value: unknown,
  label: string,
): bigint {
  if (typeof value === "bigint") {
    return value;
  }

  if (
    typeof value === "number"
    && Number.isSafeInteger(value)
  ) {
    return BigInt(value);
  }

  if (
    typeof value === "string"
    && /^[0-9]+$/.test(value)
  ) {
    return BigInt(value);
  }

  throw new Error(
    `${label} returned an unexpected value.`,
  );
}

function valueSafeNumber(
  value: unknown,
  label: string,
): number {
  const parsed =
    valueBigInt(
      value,
      label,
    );

  if (
    parsed < ZERO_BIGINT
    || parsed > BigInt(
      Number.MAX_SAFE_INTEGER,
    )
  ) {
    throw new Error(
      `${label} is outside the safe browser integer range.`,
    );
  }

  return Number(parsed);
}

function assertAddress(
  value: string,
  label: string,
): asserts value is `0x${string}` {
  if (
    !/^0x[0-9a-fA-F]{40}$/.test(value)
  ) {
    throw new Error(
      `${label} is not a valid address.`,
    );
  }
}

function assertTransactionHash(
  value: string,
): asserts value is TransactionHash {
  if (
    !/^0x[0-9a-fA-F]{64}$/.test(value)
  ) {
    throw new Error(
      "GenLayer returned an invalid transaction hash.",
    );
  }
}

export async function readClaimMissionReceipt(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<ClaimMissionReceiptSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_mission_receipt",
      args: [
        missionId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_mission_receipt",
    );

  const refundBeneficiary =
    valueString(
      record.refund_beneficiary,
      "Receipt refund beneficiary",
    );

  assertAddress(
    refundBeneficiary,
    "Receipt refund beneficiary",
  );

  return {
    missionId:
      valueString(
        record.mission_id,
        "Receipt mission ID",
      ),
    state:
      valueString(
        record.state,
        "Receipt state",
      ),
    decision:
      valueString(
        record.decision,
        "Receipt decision",
      ),
    reasonCode:
      valueString(
        record.reason_code,
        "Receipt reason code",
      ),
    allocationApplied:
      valueBoolean(
        record.allocation_applied,
        "Receipt allocation flag",
      ),
    refundBeneficiary,
    refundEntitlement:
      valueBigInt(
        record.refund_entitlement,
        "Receipt refund entitlement",
      ),
    externalWithdrawalRecovery:
      valueBoolean(
        record.external_withdrawal_recovery,
        "Receipt external-withdrawal-recovery flag",
      ),
  };
}

export async function readAggregateClaimable(
  wallet: ConnectedCommitWallet,
  beneficiary: `0x${string}`,
): Promise<bigint> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_claimable",
      args: [
        beneficiary,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  return valueBigInt(
    raw,
    "Aggregate claimable balance",
  );
}

export async function readMissionClaimable(
  wallet: ConnectedCommitWallet,
  missionId: string,
  beneficiary: `0x${string}`,
): Promise<bigint> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_mission_claimable",
      args: [
        missionId,
        beneficiary,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  return valueBigInt(
    raw,
    "Mission claimable balance",
  );
}

export async function readWithdrawalCount(
  wallet: ConnectedCommitWallet,
): Promise<number> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_withdrawal_count",
      args: [],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  return valueSafeNumber(
    raw,
    "Withdrawal count",
  );
}

function parseWithdrawal(
  raw: unknown,
  label: string,
): WithdrawalSnapshot {
  const record =
    valueRecord(
      raw,
      label,
    );

  const beneficiary =
    valueString(
      record.beneficiary,
      "Withdrawal beneficiary",
    );

  assertAddress(
    beneficiary,
    "Withdrawal beneficiary",
  );

  return {
    withdrawalId:
      valueString(
        record.withdrawal_id,
        "Withdrawal ID",
      ),
    missionId:
      valueString(
        record.mission_id,
        "Withdrawal mission ID",
      ),
    beneficiary,
    amount:
      valueBigInt(
        record.amount,
        "Withdrawal amount",
      ),
    status:
      valueString(
        record.status,
        "Withdrawal status",
      ),
  };
}

export async function readWithdrawal(
  wallet: ConnectedCommitWallet,
  withdrawalId: string,
): Promise<WithdrawalSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_withdrawal",
      args: [
        withdrawalId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  return parseWithdrawal(
    raw,
    "get_withdrawal",
  );
}

export async function readWithdrawalByIndex(
  wallet: ConnectedCommitWallet,
  index: number,
): Promise<WithdrawalSnapshot> {
  if (
    !Number.isSafeInteger(index)
    || index < 0
  ) {
    throw new Error(
      "Withdrawal index is invalid.",
    );
  }

  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_withdrawal_by_index",
      args: [
        index,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  return parseWithdrawal(
    raw,
    "get_withdrawal_by_index",
  );
}

export function validateClaimEligibility(
  snapshot: ClaimSnapshot,
): string[] {
  const errors: string[] = [];

  if (
    ![
      "COMMITTED",
      "ABORTED",
    ].includes(
      snapshot.mission.state,
    )
  ) {
    errors.push(
      "Mission must be COMMITTED or ABORTED before claiming.",
    );
  }

  if (
    !snapshot.mission.allocationApplied
  ) {
    errors.push(
      "Finalized allocation has not been applied.",
    );
  }

  if (
    snapshot.receipt.missionId
    !== snapshot.mission.missionId
    || snapshot.receipt.state
    !== snapshot.mission.state
    || snapshot.receipt.decision
    !== snapshot.mission.decision
    || snapshot.receipt.allocationApplied
    !== snapshot.mission.allocationApplied
  ) {
    errors.push(
      "Mission receipt does not match finalized mission allocation state.",
    );
  }

  if (
    snapshot.mission.state === "COMMITTED"
    && snapshot.mission.decision !== "COMMIT"
  ) {
    errors.push(
      "COMMITTED mission does not carry a COMMIT decision.",
    );
  }

  if (
    snapshot.mission.state === "ABORTED"
    && snapshot.mission.decision !== "ABORT"
  ) {
    errors.push(
      "ABORTED mission does not carry an ABORT decision.",
    );
  }

  if (
    snapshot.receipt.externalWithdrawalRecovery
  ) {
    errors.push(
      "Unexpected external withdrawal recovery mode is enabled.",
    );
  }

  if (
    snapshot.missionClaimable <= ZERO_BIGINT
  ) {
    errors.push(
      "Connected beneficiary has no claimable balance for this mission.",
    );
  }

  if (
    snapshot.aggregateClaimable
    < snapshot.missionClaimable
  ) {
    errors.push(
      "Aggregate claimable balance is below the mission entitlement.",
    );
  }

  return errors;
}

export async function readClaimSnapshot(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<ClaimSnapshot> {
  const [
    mission,
    receipt,
    missionClaimable,
    aggregateClaimable,
    withdrawalCount,
  ] = await Promise.all([
    readResolutionMission(
      wallet,
      missionId,
    ),
    readClaimMissionReceipt(
      wallet,
      missionId,
    ),
    readMissionClaimable(
      wallet,
      missionId,
      wallet.address,
    ),
    readAggregateClaimable(
      wallet,
      wallet.address,
    ),
    readWithdrawalCount(
      wallet,
    ),
  ]);

  return {
    mission,
    receipt,
    beneficiary:
      wallet.address,
    missionClaimable,
    aggregateClaimable,
    withdrawalCount,
  };
}

export async function quoteClaimMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const snapshot =
    await readClaimSnapshot(
      wallet,
      missionId,
    );

  const errors =
    validateClaimEligibility(
      snapshot,
    );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  const call = {
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName:
      "claim_mission" as const,
    args: [
      missionId,
    ],
  };

  const estimate =
    await wallet.client.estimateTransactionFeesForWrite({
      ...call,
    });

  if (
    preflight.balanceWei
    < estimate.feeValue
  ) {
    throw new Error(
      "Wallet balance is insufficient for the quoted claim transaction fee deposit.",
    );
  }

  return {
    call,
    snapshot,
    preflight,
    feeValue:
      estimate.feeValue,
    fees: {
      distribution:
        estimate.distribution,
      messageAllocations:
        estimate.messageAllocations,
      feeValue:
        estimate.feeValue,
    },
  };
}

export async function submitClaimMission(
  wallet: ConnectedCommitWallet,
  quote: ClaimMissionQuote,
): Promise<TransactionHash> {
  const txId =
    await wallet.client.writeContract({
      ...quote.call,
      fees: quote.fees,
    });

  assertTransactionHash(
    txId,
  );

  return txId;
}

function sameWithdrawal(
  left: WithdrawalSnapshot,
  right: WithdrawalSnapshot,
): boolean {
  return (
    left.withdrawalId
      === right.withdrawalId
    && left.missionId
      === right.missionId
    && left.beneficiary.toLowerCase()
      === right.beneficiary.toLowerCase()
    && left.amount
      === right.amount
    && left.status
      === right.status
  );
}

export async function verifyFinalizedClaim(
  wallet: ConnectedCommitWallet,
  quote: ClaimMissionQuote,
): Promise<FinalizedClaimProof> {
  const before =
    quote.snapshot;

  const [
    missionAfter,
    receiptAfter,
    missionClaimableAfter,
    aggregateClaimableAfter,
    withdrawalCountAfter,
  ] = await Promise.all([
    readResolutionMission(
      wallet,
      before.mission.missionId,
    ),
    readClaimMissionReceipt(
      wallet,
      before.mission.missionId,
    ),
    readMissionClaimable(
      wallet,
      before.mission.missionId,
      before.beneficiary,
    ),
    readAggregateClaimable(
      wallet,
      before.beneficiary,
    ),
    readWithdrawalCount(
      wallet,
    ),
  ]);

  if (
    !missionAfter.allocationApplied
    || missionAfter.state
      !== before.mission.state
    || missionAfter.decision
      !== before.mission.decision
    || receiptAfter.state
      !== missionAfter.state
    || receiptAfter.decision
      !== missionAfter.decision
    || !receiptAfter.allocationApplied
  ) {
    throw new Error(
      "Finalized mission allocation state changed unexpectedly during claim verification.",
    );
  }

  if (
    missionClaimableAfter
    !== ZERO_BIGINT
  ) {
    throw new Error(
      "Mission claimable balance was not zeroed after finalized claim.",
    );
  }

  const expectedAggregateUpperBound =
    before.aggregateClaimable
    - before.missionClaimable;

  if (
    aggregateClaimableAfter
    > expectedAggregateUpperBound
  ) {
    throw new Error(
      "Aggregate claimable balance did not decrease by the claimed mission amount.",
    );
  }

  if (
    withdrawalCountAfter
    <= before.withdrawalCount
  ) {
    throw new Error(
      "Finalized withdrawal count did not advance.",
    );
  }

  const delta =
    withdrawalCountAfter
    - before.withdrawalCount;

  if (delta > 64) {
    throw new Error(
      "Too many concurrent withdrawal records were added for bounded browser verification.",
    );
  }

  const candidates: WithdrawalSnapshot[] = [];

  for (
    let index = before.withdrawalCount;
    index < withdrawalCountAfter;
    index += 1
  ) {
    const withdrawal =
      await readWithdrawalByIndex(
        wallet,
        index,
      );

    if (
      withdrawal.missionId
        === before.mission.missionId
      && withdrawal.beneficiary.toLowerCase()
        === before.beneficiary.toLowerCase()
      && withdrawal.amount
        === before.missionClaimable
      && withdrawal.status
        === "DISPATCHED"
    ) {
      candidates.push(
        withdrawal,
      );
    }
  }

  if (
    candidates.length !== 1
  ) {
    throw new Error(
      "Expected exactly one matching DISPATCHED withdrawal in the finalized post-claim range.",
    );
  }

  const withdrawal =
    candidates[0];

  const direct =
    await readWithdrawal(
      wallet,
      withdrawal.withdrawalId,
    );

  if (
    !sameWithdrawal(
      withdrawal,
      direct,
    )
  ) {
    throw new Error(
      "Withdrawal direct-ID read does not match the by-index finalized record.",
    );
  }

  return {
    withdrawal,
    missionClaimableAfter,
    aggregateClaimableAfter,
    withdrawalCountAfter,
  };
}
