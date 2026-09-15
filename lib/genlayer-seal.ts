import {
  TransactionHashVariant,
  type TransactionHash,
} from "genlayer-js/types";
import {
  CURRENT_DEPLOYMENT_ANCHOR,
} from "@/lib/deployment-anchor";
import {
  preflightCommitWallet,
  readMissionEffects,
  readMissionEvidence,
  type ConnectedCommitWallet,
  type EffectSnapshot,
  type EvidenceSnapshot,
} from "@/lib/genlayer-browser";

const ZERO_BIGINT =
  BigInt(0);

export type SealMissionSnapshot = {
  missionId: string;
  principal: `0x${string}`;
  state: string;
  version: number;
  effectRoot: string;
  evidenceRoot: string;
  budget: bigint;
  fundedValue: bigint;
  preparedValue: bigint;
  effectCount: number;
  evidenceCount: number;
  prepareDeadline: number;
  recoveryDeadline: number;
};

export type IndependentEvidencePair = {
  authorityA: string;
  authorityB: string;
  issuerA: `0x${string}`;
  issuerB: `0x${string}`;
};

export type SealMissionQuote = Awaited<
  ReturnType<typeof quoteSealMission>
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

function assertDigest(
  value: string,
  label: string,
): void {
  if (
    !/^[0-9a-f]{64}$/.test(value)
  ) {
    throw new Error(
      `${label} is not a 32-byte lowercase hex digest.`,
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

export async function readSealMissionSnapshot(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<SealMissionSnapshot> {
  if (
    missionId.length === 0
    || missionId.length > 512
  ) {
    throw new Error(
      "Mission ID is invalid.",
    );
  }

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

  assertAddress(
    principal,
    "Mission principal",
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
    budget:
      valueBigInt(
        record.budget,
        "Mission budget",
      ),
    fundedValue:
      valueBigInt(
        record.funded_value,
        "Mission funded value",
      ),
    preparedValue:
      valueBigInt(
        record.prepared_value,
        "Mission prepared value",
      ),
    effectCount:
      valueSafeNumber(
        record.effect_count,
        "Mission effect count",
      ),
    evidenceCount:
      valueSafeNumber(
        record.evidence_count,
        "Mission evidence count",
      ),
    prepareDeadline:
      valueSafeNumber(
        record.prepare_deadline,
        "Mission preparation deadline",
      ),
    recoveryDeadline:
      valueSafeNumber(
        record.recovery_deadline,
        "Mission recovery deadline",
      ),
  };
}

export function validateEffectGraph(
  effects: EffectSnapshot[],
): string[] {
  const errors: string[] = [];
  const byId =
    new Map(
      effects.map(
        (effect) => [
          effect.effectId,
          effect,
        ],
      ),
    );

  if (
    byId.size !== effects.length
  ) {
    errors.push(
      "Prepared effect IDs are not unique.",
    );
  }

  for (
    const effect
    of effects
  ) {
    let dependency =
      effect.dependencyId;

    const visited =
      new Set<string>([
        effect.effectId,
      ]);

    while (
      dependency.length > 0
    ) {
      const parent =
        byId.get(dependency);

      if (parent === undefined) {
        errors.push(
          `Dependency effect not found: ${dependency}.`,
        );
        break;
      }

      if (
        visited.has(dependency)
      ) {
        errors.push(
          "Effect graph contains a cycle.",
        );
        break;
      }

      visited.add(dependency);

      if (
        visited.size > effects.length
      ) {
        errors.push(
          "Effect graph contains a cycle.",
        );
        break;
      }

      dependency =
        parent.dependencyId;
    }
  }

  return [
    ...new Set(errors),
  ];
}

export async function readAuthorityIndependence(
  wallet: ConnectedCommitWallet,
  authorityA: string,
  authorityB: string,
): Promise<boolean> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "authorities_are_independent",
      args: [
        authorityA,
        authorityB,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  if (typeof raw !== "boolean") {
    throw new Error(
      "Authority independence read returned an unexpected value.",
    );
  }

  return raw;
}

export async function findIndependentEvidencePair(
  wallet: ConnectedCommitWallet,
  evidence: EvidenceSnapshot[],
): Promise<IndependentEvidencePair | null> {
  for (
    let left = 0;
    left < evidence.length;
    left += 1
  ) {
    for (
      let right = left + 1;
      right < evidence.length;
      right += 1
    ) {
      const first =
        evidence[left];
      const second =
        evidence[right];

      if (
        first.authorityId === second.authorityId
        || first.issuerAddress.toLowerCase()
        === second.issuerAddress.toLowerCase()
      ) {
        continue;
      }

      const independent =
        await readAuthorityIndependence(
          wallet,
          first.authorityId,
          second.authorityId,
        );

      if (independent) {
        return {
          authorityA:
            first.authorityId,
          authorityB:
            second.authorityId,
          issuerA:
            first.issuerAddress,
          issuerB:
            second.issuerAddress,
        };
      }
    }
  }

  return null;
}

export function validateSealMissionEligibility(
  mission: SealMissionSnapshot,
  walletAddress: `0x${string}`,
  effects: EffectSnapshot[],
  evidence: EvidenceSnapshot[],
  independentPair:
    IndependentEvidencePair | null,
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
      "Only the mission principal can seal this mission.",
    );
  }

  if (
    mission.state !== "PREPARING"
  ) {
    errors.push(
      "Mission must still be PREPARING to seal.",
    );
  }

  if (
    nowSeconds > mission.prepareDeadline
  ) {
    errors.push(
      "The mission preparation deadline has passed.",
    );
  }

  if (
    effects.length === 0
  ) {
    errors.push(
      "Mission has no prepared effects.",
    );
  }

  if (
    evidence.length < 2
  ) {
    errors.push(
      "Mission needs at least two registered evidence records.",
    );
  }

  if (
    mission.fundedValue
    < mission.preparedValue
  ) {
    errors.push(
      "Mission is underfunded for its prepared effects.",
    );
  }

  const distinctIssuers =
    new Set(
      evidence.map(
        (item) => (
          item.issuerAddress.toLowerCase()
        ),
      ),
    );

  if (
    distinctIssuers.size < 2
  ) {
    errors.push(
      "Registered evidence must use at least two distinct issuer identities.",
    );
  }

  if (
    independentPair === null
  ) {
    errors.push(
      "No independent authority pair was verified for corroboration.",
    );
  }

  errors.push(
    ...validateEffectGraph(effects),
  );

  return [
    ...new Set(errors),
  ];
}

export async function deriveSealRoots(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<{
  effectRoot: string;
  evidenceRoot: string;
}> {
  const [
    effectRaw,
    evidenceRaw,
  ] = await Promise.all([
    wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "derive_effect_root",
      args: [
        missionId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    }),
    wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "derive_evidence_root",
      args: [
        missionId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    }),
  ]);

  const effectRoot =
    valueString(
      effectRaw,
      "Derived effect root",
    );
  const evidenceRoot =
    valueString(
      evidenceRaw,
      "Derived evidence root",
    );

  assertDigest(
    effectRoot,
    "Derived effect root",
  );
  assertDigest(
    evidenceRoot,
    "Derived evidence root",
  );

  return {
    effectRoot,
    evidenceRoot,
  };
}

export async function quoteSealMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
) {
  const preflight =
    await preflightCommitWallet(wallet);

  const mission =
    await readSealMissionSnapshot(
      wallet,
      missionId,
    );

  const [
    effects,
    evidence,
  ] = await Promise.all([
    readMissionEffects(
      wallet,
      missionId,
      mission.effectCount,
    ),
    readMissionEvidence(
      wallet,
      missionId,
      mission.evidenceCount,
    ),
  ]);

  const independentPair =
    await findIndependentEvidencePair(
      wallet,
      evidence,
    );

  const errors =
    validateSealMissionEligibility(
      mission,
      wallet.address,
      effects,
      evidence,
      independentPair,
    );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  const roots =
    await deriveSealRoots(
      wallet,
      missionId,
    );

  const call = {
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName:
      "seal_mission" as const,
    args: [
      missionId,
      roots.effectRoot,
      roots.evidenceRoot,
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
      "Wallet balance is insufficient for the quoted mission-seal fee deposit.",
    );
  }

  return {
    call,
    mission,
    effects,
    evidence,
    independentPair:
      independentPair as IndependentEvidencePair,
    roots,
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

export async function submitSealMission(
  wallet: ConnectedCommitWallet,
  quote: SealMissionQuote,
): Promise<TransactionHash> {
  const txId =
    await wallet.client.writeContract({
      ...quote.call,
      fees: quote.fees,
    });

  assertTransactionHash(txId);

  return txId;
}

export async function verifyFinalizedSeal(
  wallet: ConnectedCommitWallet,
  missionId: string,
  expectedEffectRoot: string,
  expectedEvidenceRoot: string,
): Promise<SealMissionSnapshot> {
  const mission =
    await readSealMissionSnapshot(
      wallet,
      missionId,
    );

  if (
    mission.state !== "SEALED"
  ) {
    throw new Error(
      "Finalized mission state is not SEALED.",
    );
  }

  if (
    mission.effectRoot !== expectedEffectRoot
    || mission.evidenceRoot !== expectedEvidenceRoot
  ) {
    throw new Error(
      "Finalized mission roots do not match the reviewed seal roots.",
    );
  }

  return mission;
}
