import {
  TransactionHashVariant,
  type TransactionHash,
} from "genlayer-js/types";
import {
  CURRENT_DEPLOYMENT_ANCHOR,
} from "@/lib/deployment-anchor";
import {
  preflightCommitWallet,
  readEvidence,
  readEvidenceAttestation,
  type ConnectedCommitWallet,
  type EvidenceAttestationSnapshot,
  type EvidenceSnapshot,
} from "@/lib/genlayer-browser";

const ZERO_BIGINT =
  BigInt(0);

export type ResolutionMissionSnapshot = {
  missionId: string;
  principal: `0x${string}`;
  state: string;
  version: number;
  decision: string;
  reasonCode: string;
  decisionNonce: string;
  effectRoot: string;
  evidenceRoot: string;
  evaluationEvidenceRoot: string;
  allocationApplied: boolean;
  refundBeneficiary: `0x${string}`;
  refundEntitlement: bigint;
  evaluationCount: number;
  evidenceCount: number;
  recoveryDeadline: number;
};

export type MissionReceiptSnapshot = {
  receiptSchema: string;
  manifestSchema: string;
  protocol: string;
  revision: string;
  chainId: number;
  coordinator: `0x${string}`;
  missionId: string;
  principal: `0x${string}`;
  version: number;
  state: string;
  decision: string;
  reasonCode: string;
  decisionNonce: string;
  effectRoot: string;
  evidenceRoot: string;
  evaluationEvidenceRoot: string;
  effectCount: number;
  evidenceCount: number;
  budget: bigint;
  fundedValue: bigint;
  preparedValue: bigint;
  refundBeneficiary: `0x${string}`;
  refundEntitlement: bigint;
  recoveryDeadline: number;
  evaluationCount: number;
  allocationApplied: boolean;
};

export type EvidenceFailureSnapshot = {
  status: string;
  failureCode: string;
  evidenceId: string;
  recordId: string;
  failedRecordVersion: number;
  missionVersion: number;
  attempt: number;
};

export type EvidenceRepairSnapshot = {
  status: string;
  authorityId: string;
  authorityVersion: number;
  issuerAddress: `0x${string}`;
  recordId: string;
  originalRecordVersion: number;
  activeRecordVersion: number;
  url: string;
  recordHash: string;
  publishedAt: number;
  expiresAt: number;
};

export type RepairEvidenceDraft = {
  missionId: string;
  evidenceId: string;
  recordVersion: number;
};

export type ResolutionInspection = {
  mission: ResolutionMissionSnapshot;
  receipt: MissionReceiptSnapshot;
  classification:
    | "SEALED"
    | "DECISION_PENDING"
    | "ALLOCATED_COMMIT"
    | "ALLOCATED_ABORT"
    | "OTHER";
};

export type EvaluateMissionQuote = Awaited<
  ReturnType<typeof quoteEvaluateMission>
>;

export type RepairEvidenceQuote = Awaited<
  ReturnType<typeof quoteRepairEvidence>
>;

export type ExpireMissionQuote = Awaited<
  ReturnType<typeof quoteExpireMission>
>;

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
  const bigintValue =
    valueBigInt(
      value,
      label,
    );

  if (
    bigintValue < ZERO_BIGINT
    || bigintValue > BigInt(
      Number.MAX_SAFE_INTEGER,
    )
  ) {
    throw new Error(
      `${label} is outside the safe browser integer range.`,
    );
  }

  return Number(bigintValue);
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

export async function readResolutionMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<ResolutionMissionSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_mission",
      args: [
        missionId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_mission",
    );

  const principal =
    valueString(
      record.principal,
      "Mission principal",
    );
  const refundBeneficiary =
    valueString(
      record.refund_beneficiary,
      "Refund beneficiary",
    );

  assertAddress(
    principal,
    "Mission principal",
  );
  assertAddress(
    refundBeneficiary,
    "Refund beneficiary",
  );

  return {
    missionId:
      valueString(
        record.mission_id,
        "Mission ID",
      ),
    principal,
    state:
      valueString(
        record.state,
        "Mission state",
      ),
    version:
      valueSafeNumber(
        record.version,
        "Mission version",
      ),
    decision:
      valueString(
        record.decision,
        "Mission decision",
      ),
    reasonCode:
      valueString(
        record.reason_code,
        "Mission reason code",
      ),
    decisionNonce:
      valueString(
        record.decision_nonce,
        "Mission decision nonce",
      ),
    effectRoot:
      valueString(
        record.effect_root,
        "Mission effect root",
      ),
    evidenceRoot:
      valueString(
        record.evidence_root,
        "Mission evidence root",
      ),
    evaluationEvidenceRoot:
      valueString(
        record.evaluation_evidence_root,
        "Mission evaluation evidence root",
      ),
    allocationApplied:
      valueBoolean(
        record.allocation_applied,
        "Mission allocation flag",
      ),
    refundBeneficiary,
    refundEntitlement:
      valueBigInt(
        record.refund_entitlement,
        "Mission refund entitlement",
      ),
    evaluationCount:
      valueSafeNumber(
        record.evaluation_count,
        "Mission evaluation count",
      ),
    evidenceCount:
      valueSafeNumber(
        record.evidence_count,
        "Mission evidence count",
      ),
    recoveryDeadline:
      valueSafeNumber(
        record.recovery_deadline,
        "Mission recovery deadline",
      ),
  };
}

export async function readMissionReceipt(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<MissionReceiptSnapshot> {
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

  const coordinator =
    valueString(
      record.coordinator,
      "Receipt coordinator",
    );
  const principal =
    valueString(
      record.principal,
      "Receipt principal",
    );
  const refundBeneficiary =
    valueString(
      record.refund_beneficiary,
      "Receipt refund beneficiary",
    );

  assertAddress(
    coordinator,
    "Receipt coordinator",
  );
  assertAddress(
    principal,
    "Receipt principal",
  );
  assertAddress(
    refundBeneficiary,
    "Receipt refund beneficiary",
  );

  return {
    receiptSchema:
      valueString(
        record.receipt_schema,
        "Receipt schema",
      ),
    manifestSchema:
      valueString(
        record.manifest_schema,
        "Manifest schema",
      ),
    protocol:
      valueString(
        record.protocol,
        "Receipt protocol",
      ),
    revision:
      valueString(
        record.revision,
        "Receipt revision",
      ),
    chainId:
      valueSafeNumber(
        record.chain_id,
        "Receipt chain ID",
      ),
    coordinator,
    missionId:
      valueString(
        record.mission_id,
        "Receipt mission ID",
      ),
    principal,
    version:
      valueSafeNumber(
        record.version,
        "Receipt mission version",
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
    decisionNonce:
      valueString(
        record.decision_nonce,
        "Receipt decision nonce",
      ),
    effectRoot:
      valueString(
        record.effect_root,
        "Receipt effect root",
      ),
    evidenceRoot:
      valueString(
        record.evidence_root,
        "Receipt evidence root",
      ),
    evaluationEvidenceRoot:
      valueString(
        record.evaluation_evidence_root,
        "Receipt evaluation evidence root",
      ),
    effectCount:
      valueSafeNumber(
        record.effect_count,
        "Receipt effect count",
      ),
    evidenceCount:
      valueSafeNumber(
        record.evidence_count,
        "Receipt evidence count",
      ),
    budget:
      valueBigInt(
        record.budget,
        "Receipt budget",
      ),
    fundedValue:
      valueBigInt(
        record.funded_value,
        "Receipt funded value",
      ),
    preparedValue:
      valueBigInt(
        record.prepared_value,
        "Receipt prepared value",
      ),
    refundBeneficiary,
    refundEntitlement:
      valueBigInt(
        record.refund_entitlement,
        "Receipt refund entitlement",
      ),
    recoveryDeadline:
      valueSafeNumber(
        record.recovery_deadline,
        "Receipt recovery deadline",
      ),
    evaluationCount:
      valueSafeNumber(
        record.evaluation_count,
        "Receipt evaluation count",
      ),
    allocationApplied:
      valueBoolean(
        record.allocation_applied,
        "Receipt allocation flag",
      ),
  };
}

export async function readEvidenceFailure(
  wallet: ConnectedCommitWallet,
  missionId: string,
  evidenceId: string,
): Promise<EvidenceFailureSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_evidence_failure",
      args: [
        missionId,
        evidenceId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_evidence_failure",
    );

  return {
    status:
      valueString(
        record.status,
        "Evidence failure status",
      ),
    failureCode:
      valueString(
        record.failure_code,
        "Evidence failure code",
      ),
    evidenceId:
      valueString(
        record.evidence_id,
        "Evidence failure ID",
      ),
    recordId:
      valueString(
        record.record_id,
        "Evidence failure record ID",
      ),
    failedRecordVersion:
      valueSafeNumber(
        record.failed_record_version,
        "Failed record version",
      ),
    missionVersion:
      valueSafeNumber(
        record.mission_version,
        "Failure mission version",
      ),
    attempt:
      valueSafeNumber(
        record.attempt,
        "Evidence failure attempt",
      ),
  };
}

export async function readEvidenceRepair(
  wallet: ConnectedCommitWallet,
  missionId: string,
  evidenceId: string,
): Promise<EvidenceRepairSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_evidence_repair",
      args: [
        missionId,
        evidenceId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_evidence_repair",
    );

  const issuerAddress =
    valueString(
      record.issuer_address,
      "Repair issuer",
    );

  assertAddress(
    issuerAddress,
    "Repair issuer",
  );

  return {
    status:
      valueString(
        record.status,
        "Repair status",
      ),
    authorityId:
      valueString(
        record.authority_id,
        "Repair authority ID",
      ),
    authorityVersion:
      valueSafeNumber(
        record.authority_version,
        "Repair authority version",
      ),
    issuerAddress,
    recordId:
      valueString(
        record.record_id,
        "Repair record ID",
      ),
    originalRecordVersion:
      valueSafeNumber(
        record.original_record_version,
        "Original record version",
      ),
    activeRecordVersion:
      valueSafeNumber(
        record.active_record_version,
        "Active record version",
      ),
    url:
      valueString(
        record.url,
        "Repair URL",
      ),
    recordHash:
      valueString(
        record.record_hash,
        "Repair record hash",
      ),
    publishedAt:
      valueSafeNumber(
        record.published_at,
        "Repair publication time",
      ),
    expiresAt:
      valueSafeNumber(
        record.expires_at,
        "Repair expiry time",
      ),
  };
}

export async function inspectResolutionState(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<ResolutionInspection> {
  const [
    mission,
    receipt,
  ] = await Promise.all([
    readResolutionMission(
      wallet,
      missionId,
    ),
    readMissionReceipt(
      wallet,
      missionId,
    ),
  ]);

  let classification:
    ResolutionInspection["classification"] =
      "OTHER";

  if (
    mission.state === "SEALED"
    && !mission.allocationApplied
  ) {
    classification =
      "SEALED";
  } else if (
    mission.state === "DECISION_PENDING"
    && !mission.allocationApplied
  ) {
    classification =
      "DECISION_PENDING";
  } else if (
    mission.state === "COMMITTED"
    && mission.decision === "COMMIT"
    && mission.allocationApplied
  ) {
    classification =
      "ALLOCATED_COMMIT";
  } else if (
    mission.state === "ABORTED"
    && mission.decision === "ABORT"
    && mission.allocationApplied
  ) {
    classification =
      "ALLOCATED_ABORT";
  }

  return {
    mission,
    receipt,
    classification,
  };
}

export function validateEvaluateEligibility(
  mission: ResolutionMissionSnapshot,
  nowSeconds = Math.floor(
    Date.now() / 1000,
  ),
): string[] {
  const errors: string[] = [];

  if (
    mission.state !== "SEALED"
  ) {
    errors.push(
      "Mission must be SEALED before evaluation.",
    );
  }

  if (
    mission.decision.length > 0
  ) {
    errors.push(
      "Mission already has a consensus decision.",
    );
  }

  if (
    nowSeconds >= mission.recoveryDeadline
  ) {
    errors.push(
      "Recovery deadline has passed; evaluate_mission is no longer available.",
    );
  }

  return errors;
}

export function validateRepairEligibility(
  mission: ResolutionMissionSnapshot,
  walletAddress: `0x${string}`,
  evidence: EvidenceSnapshot,
  failure: EvidenceFailureSnapshot,
  attestation: EvidenceAttestationSnapshot,
  newRecordVersion: number,
  nowSeconds = Math.floor(
    Date.now() / 1000,
  ),
): string[] {
  const errors: string[] = [];

  if (
    mission.principal.toLowerCase()
    !== walletAddress.toLowerCase()
  ) {
    errors.push(
      "Only the mission principal can repair evidence.",
    );
  }

  if (
    mission.state !== "SEALED"
  ) {
    errors.push(
      "Mission must remain SEALED to repair evidence.",
    );
  }

  if (
    mission.decision.length > 0
  ) {
    errors.push(
      "Mission already has a consensus decision.",
    );
  }

  if (
    nowSeconds >= mission.recoveryDeadline
  ) {
    errors.push(
      "Recovery deadline has passed; evidence repair is closed.",
    );
  }

  if (
    failure.status !== "REPAIR_REQUIRED"
  ) {
    errors.push(
      "Evidence does not have a REPAIR_REQUIRED failure.",
    );
  }

  if (
    failure.evidenceId !== evidence.evidenceId
    || failure.recordId !== evidence.recordId
    || failure.missionVersion !== evidence.missionVersion
  ) {
    errors.push(
      "Evidence failure identity does not match the registered evidence.",
    );
  }

  if (
    !Number.isSafeInteger(
      newRecordVersion,
    )
    || newRecordVersion <= failure.failedRecordVersion
  ) {
    errors.push(
      "Repair record version must be newer than the failed active record version.",
    );
  }

  if (
    attestation.authorityId !== evidence.authorityId
    || attestation.authorityVersion !== evidence.authorityVersion
  ) {
    errors.push(
      "Repair attestation authority identity/version does not match the registered evidence.",
    );
  }

  if (
    attestation.issuerAddress.toLowerCase()
    !== evidence.issuerAddress.toLowerCase()
  ) {
    errors.push(
      "Repair attestation issuer does not match the original evidence issuer.",
    );
  }

  if (
    attestation.recordId !== evidence.recordId
    || attestation.recordVersion !== newRecordVersion
  ) {
    errors.push(
      "Repair attestation record identity/version does not match the requested repair.",
    );
  }

  if (
    attestation.missionId !== mission.missionId
    || attestation.missionVersion !== mission.version
  ) {
    errors.push(
      "Repair attestation mission identity/version does not match finalized mission state.",
    );
  }

  return errors;
}

export function validateExpireEligibility(
  mission: ResolutionMissionSnapshot,
  nowSeconds = Math.floor(
    Date.now() / 1000,
  ),
): string[] {
  const errors: string[] = [];

  if (
    ![
      "PREPARING",
      "SEALED",
      "DECISION_PENDING",
    ].includes(
      mission.state,
    )
  ) {
    errors.push(
      "Mission is already terminal and cannot be expired.",
    );
  }

  if (
    nowSeconds < mission.recoveryDeadline
  ) {
    errors.push(
      "Recovery deadline has not passed.",
    );
  }

  return errors;
}

export async function quoteEvaluateMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
) {
  const preflight =
    await preflightCommitWallet(wallet);
  const mission =
    await readResolutionMission(
      wallet,
      missionId,
    );

  const errors =
    validateEvaluateEligibility(
      mission,
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
      "evaluate_mission" as const,
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
      "Wallet balance is insufficient for the quoted evaluation fee deposit.",
    );
  }

  return {
    call,
    mission,
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

export async function submitEvaluateMission(
  wallet: ConnectedCommitWallet,
  quote: EvaluateMissionQuote,
): Promise<TransactionHash> {
  const txId =
    await wallet.client.writeContract({
      ...quote.call,
      fees: quote.fees,
    });

  assertTransactionHash(txId);

  return txId;
}

export async function quoteRepairEvidence(
  wallet: ConnectedCommitWallet,
  draft: RepairEvidenceDraft,
) {
  const preflight =
    await preflightCommitWallet(wallet);

  const mission =
    await readResolutionMission(
      wallet,
      draft.missionId,
    );

  const evidence =
    await readEvidence(
      wallet,
      draft.missionId,
      draft.evidenceId,
    );

  const failure =
    await readEvidenceFailure(
      wallet,
      draft.missionId,
      draft.evidenceId,
    );

  const attestation =
    await readEvidenceAttestation(
      wallet,
      evidence.authorityId,
      evidence.recordId,
      draft.recordVersion,
    );

  const errors =
    validateRepairEligibility(
      mission,
      wallet.address,
      evidence,
      failure,
      attestation,
      draft.recordVersion,
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
      "repair_evidence" as const,
    args: [
      draft.missionId,
      draft.evidenceId,
      evidence.authorityId,
      evidence.authorityVersion,
      evidence.recordId,
      draft.recordVersion,
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
      "Wallet balance is insufficient for the quoted evidence-repair fee deposit.",
    );
  }

  return {
    call,
    mission,
    evidence,
    failure,
    attestation,
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

export async function submitRepairEvidence(
  wallet: ConnectedCommitWallet,
  quote: RepairEvidenceQuote,
): Promise<TransactionHash> {
  const txId =
    await wallet.client.writeContract({
      ...quote.call,
      fees: quote.fees,
    });

  assertTransactionHash(txId);

  return txId;
}

export async function verifyFinalizedRepair(
  wallet: ConnectedCommitWallet,
  missionId: string,
  evidenceId: string,
  expectedRecordVersion: number,
): Promise<EvidenceRepairSnapshot> {
  const repair =
    await readEvidenceRepair(
      wallet,
      missionId,
      evidenceId,
    );

  if (
    repair.status !== "READY"
    || repair.activeRecordVersion
    !== expectedRecordVersion
  ) {
    throw new Error(
      "Finalized evidence repair does not match the reviewed record version.",
    );
  }

  return repair;
}

export async function quoteExpireMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
) {
  const preflight =
    await preflightCommitWallet(wallet);
  const mission =
    await readResolutionMission(
      wallet,
      missionId,
    );

  const errors =
    validateExpireEligibility(
      mission,
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
      "expire_mission" as const,
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
      "Wallet balance is insufficient for the quoted recovery transaction fee deposit.",
    );
  }

  return {
    call,
    mission,
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

export async function submitExpireMission(
  wallet: ConnectedCommitWallet,
  quote: ExpireMissionQuote,
): Promise<TransactionHash> {
  const txId =
    await wallet.client.writeContract({
      ...quote.call,
      fees: quote.fees,
    });

  assertTransactionHash(txId);

  return txId;
}

export async function verifyFinalizedRecovery(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<ResolutionInspection> {
  const inspection =
    await inspectResolutionState(
      wallet,
      missionId,
    );

  if (
    inspection.classification !== "ALLOCATED_ABORT"
    || inspection.mission.reasonCode
    !== "recovery_deadline_expired"
    || !inspection.mission.allocationApplied
  ) {
    throw new Error(
      "Finalized recovery did not produce the expected allocated ABORT state.",
    );
  }

  return inspection;
}
