import {
  createClient,
} from "genlayer-js";
import {
  studioDevnet,
} from "genlayer-js/chains";
import {
  ExecutionResult,
  TransactionHashVariant,
  TransactionStatus,
  type TransactionHash,
} from "genlayer-js/types";
import {
  CURRENT_DEPLOYMENT_ANCHOR,
} from "@/lib/deployment-anchor";

export const COMMIT_POLICY_DIGEST =
  "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103";

export const STUDIO_DEV_CHAIN_ID = 61997;
export const STUDIO_DEV_CHAIN_HEX = "0xf22d";
export const GEN_DECIMALS = 18;

const GEN_BASE_UNITS = BigInt(
  "1000000000000000000",
);
const ZERO_BIGINT = BigInt(0);

type ProviderRequest = {
  method: string;
  params?: readonly unknown[] | Record<string, unknown>;
};

export type BrowserProvider = {
  request: (
    args: ProviderRequest,
  ) => Promise<unknown>;
  on?: (
    event: string,
    listener: (...args: unknown[]) => void,
  ) => void;
  removeListener?: (
    event: string,
    listener: (...args: unknown[]) => void,
  ) => void;
};

export type MissionDraft = {
  missionId: string;
  objective: string;
  budgetGen: string;
  refundBeneficiary: string;
  prepareDeadline: number;
  recoveryDeadline: number;
};

export type ConnectedCommitWallet = {
  address: `0x${string}`;
  provider: BrowserProvider;
  client: ReturnType<typeof createClient>;
};

export type CreateMissionQuote = Awaited<
  ReturnType<typeof quoteCreateMission>
>;

export type WalletPreflight = {
  account: `0x${string}`;
  chainId: number;
  balanceWei: bigint;
  balanceGen: string;
};

export type MissionFundingSnapshot = {
  missionId: string;
  principal: `0x${string}`;
  state: string;
  objective: string;
  budget: bigint;
  fundedValue: bigint;
  preparedValue: bigint;
  effectCount: number;
  supplierCount: number;
  prepareDeadline: number;
  recoveryDeadline: number;
};

export type EffectSnapshot = {
  missionId: string;
  effectId: string;
  supplier: `0x${string}`;
  digest: string;
  dependencyId: string;
  beneficiary: `0x${string}`;
  value: bigint;
  expiry: number;
};

export type PrepareEffectDraft = {
  missionId: string;
  effectId: string;
  effectDigest: string;
  beneficiary: string;
  valueGen: string;
  expiry: number;
  dependencyId: string;
};

export type FundMissionQuote = Awaited<
  ReturnType<typeof quoteFundMission>
>;

export type SupplierAuthorizationQuote = Awaited<
  ReturnType<typeof quoteSupplierAuthorization>
>;

export type PrepareEffectQuote = Awaited<
  ReturnType<typeof quotePrepareEffect>
>;

export type MissionEvidenceContext = {
  missionId: string;
  principal: `0x${string}`;
  state: string;
  version: number;
  evidenceCount: number;
  prepareDeadline: number;
  recoveryDeadline: number;
  createdAt: number;
};

export type AuthoritySnapshot = {
  authorityId: string;
  active: boolean;
  host: string;
  pathPrefix: string;
  issuerAddress: `0x${string}`;
  authorityVersion: number;
};

export type EvidenceAttestationSnapshot = {
  authorityId: string;
  authorityVersion: number;
  issuerAddress: `0x${string}`;
  recordId: string;
  recordVersion: number;
  missionId: string;
  missionVersion: number;
  url: string;
  recordHash: string;
  publishedAt: number;
  expiresAt: number;
};

export type EvidenceSnapshot = {
  missionId: string;
  evidenceId: string;
  authorityId: string;
  authorityVersion: number;
  issuerAddress: `0x${string}`;
  recordId: string;
  recordVersion: number;
  missionVersion: number;
  url: string;
  recordHash: string;
  subject: string;
  publishedAt: number;
  expiresAt: number;
};

export type AttestEvidenceDraft = {
  missionId: string;
  authorityId: string;
  recordId: string;
  recordVersion: number;
  url: string;
  recordHash: string;
  publishedAt: number;
  expiresAt: number;
};

export type RegisterEvidenceDraft = {
  missionId: string;
  evidenceId: string;
  authorityId: string;
  recordId: string;
  recordVersion: number;
};

export type AttestEvidenceQuote = Awaited<
  ReturnType<typeof quoteAttestEvidence>
>;

export type RegisterEvidenceQuote = Awaited<
  ReturnType<typeof quoteRegisterEvidence>
>;

export type TransactionProgress =
  | {
      phase: "submitted";
      txId: TransactionHash;
    }
  | {
      phase: "accepted";
      txId: TransactionHash;
      statusName: string;
      executionResultName: string;
    }
  | {
      phase: "finalized";
      txId: TransactionHash;
      statusName: string;
      executionResultName: string;
      successful: boolean;
    };

function assertAddress(
  value: string,
  label: string,
): asserts value is `0x${string}` {
  if (!/^0x[0-9a-fA-F]{40}$/.test(value)) {
    throw new Error(`${label} must be a 20-byte EVM address.`);
  }

  if (/^0x0{40}$/i.test(value)) {
    throw new Error(`${label} cannot be the zero address.`);
  }
}

function browserProvider(): BrowserProvider {
  if (typeof window === "undefined") {
    throw new Error("Wallet connection is available only in the browser.");
  }

  const candidate = (
    window as typeof window & {
      ethereum?: BrowserProvider;
    }
  ).ethereum;

  if (candidate === undefined) {
    throw new Error(
      "No MetaMask-compatible browser wallet was detected. Install or enable a wallet that supports the GenLayer Snap.",
    );
  }

  return candidate;
}

function receiptText(
  value: unknown,
  key: string,
): string {
  if (
    typeof value === "object"
    && value !== null
    && key in value
  ) {
    const candidate = (
      value as Record<string, unknown>
    )[key];

    if (
      typeof candidate === "string"
      || typeof candidate === "number"
      || typeof candidate === "bigint"
    ) {
      return String(candidate);
    }
  }

  return "Unknown";
}

export function parseGenAmount(
  value: string,
): bigint {
  const normalized = value.trim();

  if (!/^(?:0|[1-9]\d*)(?:\.\d{1,18})?$/.test(normalized)) {
    throw new Error(
      "Budget must be a positive GEN amount with at most 18 decimal places.",
    );
  }

  const [whole, fraction = ""] = normalized.split(".");
  const padded = fraction.padEnd(GEN_DECIMALS, "0");
  const units = (
    BigInt(whole) * GEN_BASE_UNITS
  ) + BigInt(padded || "0");

  if (units <= ZERO_BIGINT) {
    throw new Error("Budget must be greater than zero.");
  }

  return units;
}

export function formatGenAmount(
  value: bigint,
  maxFractionDigits = 6,
): string {
  const base = GEN_BASE_UNITS;
  const whole = value / base;
  const fraction = (
    value % base
  )
    .toString()
    .padStart(GEN_DECIMALS, "0")
    .slice(0, maxFractionDigits)
    .replace(/0+$/, "");

  return fraction.length > 0
    ? `${whole}.${fraction}`
    : whole.toString();
}

export function validateMissionDraft(
  draft: MissionDraft,
): string[] {
  const errors: string[] = [];

  if (
    draft.missionId.length === 0
    || draft.missionId.length > 512
    || draft.missionId.includes(":")
    || [...draft.missionId].some(
      (character) => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
      },
    )
  ) {
    errors.push(
      "Mission ID must be printable ASCII, 1-512 characters, with no colon.",
    );
  }

  if (
    draft.objective.length === 0
    || draft.objective.length > 512
    || [...draft.objective].some(
      (character) => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
      },
    )
  ) {
    errors.push(
      "Objective must be printable ASCII and 1-512 characters.",
    );
  }

  try {
    parseGenAmount(
      draft.budgetGen,
    );
  } catch (error: unknown) {
    errors.push(
      error instanceof Error
        ? error.message
        : "Budget is invalid.",
    );
  }

  try {
    assertAddress(
      draft.refundBeneficiary,
      "Refund beneficiary",
    );
  } catch (error: unknown) {
    errors.push(
      error instanceof Error
        ? error.message
        : "Refund beneficiary is invalid.",
    );
  }

  const now = Math.floor(
    Date.now() / 1000,
  );

  if (
    !Number.isSafeInteger(
      draft.prepareDeadline,
    )
    || draft.prepareDeadline <= now
  ) {
    errors.push(
      "Preparation deadline must be a future Unix timestamp.",
    );
  }

  if (
    !Number.isSafeInteger(
      draft.recoveryDeadline,
    )
    || draft.recoveryDeadline <= draft.prepareDeadline
  ) {
    errors.push(
      "Recovery deadline must be later than the preparation deadline.",
    );
  }

  return errors;
}

export async function connectCommitWallet(): Promise<ConnectedCommitWallet> {
  const provider = browserProvider();

  const accounts = await provider.request({
    method: "eth_requestAccounts",
  });

  if (
    !Array.isArray(accounts)
    || typeof accounts[0] !== "string"
  ) {
    throw new Error(
      "The wallet did not return an account.",
    );
  }

  const address = accounts[0];
  assertAddress(
    address,
    "Wallet account",
  );

  const client = createClient({
    chain: studioDevnet,
    account: address,
    provider: provider as never,
  });

  await client.connect(
    "studioDevnet",
  );

  const chainId = await provider.request({
    method: "eth_chainId",
  });

  if (
    typeof chainId !== "string"
    || chainId.toLowerCase() !== STUDIO_DEV_CHAIN_HEX
  ) {
    throw new Error(
      `Wallet must be connected to GenLayer Studio-dev (${STUDIO_DEV_CHAIN_ID}).`,
    );
  }

  return {
    address,
    provider,
    client,
  };
}

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
      `${label} returned an unexpected shape.`,
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
    && value >= 0
  ) {
    return BigInt(value);
  }

  if (
    typeof value === "string"
    && /^\d+$/.test(value)
  ) {
    return BigInt(value);
  }

  throw new Error(
    `${label} returned an invalid integer.`,
  );
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

function valueSafeNumber(
  value: unknown,
  label: string,
): number {
  const parsed = valueBigInt(
    value,
    label,
  );

  const number = Number(
    parsed,
  );

  if (!Number.isSafeInteger(number)) {
    throw new Error(
      `${label} exceeds the browser safe-integer range.`,
    );
  }

  return number;
}

function validateMissionIdentifier(
  missionId: string,
): void {
  if (
    missionId.length === 0
    || missionId.length > 512
    || missionId.includes(":")
    || [...missionId].some(
      (character) => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
      },
    )
  ) {
    throw new Error(
      "Mission ID must be printable ASCII, 1-512 characters, with no colon.",
    );
  }
}

export async function preflightCommitWallet(
  wallet: ConnectedCommitWallet,
): Promise<WalletPreflight> {
  const chainId = await wallet.provider.request({
    method: "eth_chainId",
  });

  if (
    typeof chainId !== "string"
    || chainId.toLowerCase() !== STUDIO_DEV_CHAIN_HEX
  ) {
    throw new Error(
      `Wallet is not on GenLayer Studio-dev (${STUDIO_DEV_CHAIN_ID}).`,
    );
  }

  const accounts = await wallet.provider.request({
    method: "eth_accounts",
  });

  if (
    !Array.isArray(accounts)
    || !accounts.some(
      (account) => (
        typeof account === "string"
        && account.toLowerCase()
        === wallet.address.toLowerCase()
      ),
    )
  ) {
    throw new Error(
      "The connected wallet account is no longer authorized.",
    );
  }

  const balanceRaw = await wallet.provider.request({
    method: "eth_getBalance",
    params: [
      wallet.address,
      "latest",
    ],
  });

  if (
    typeof balanceRaw !== "string"
    || !/^0x[0-9a-fA-F]+$/.test(balanceRaw)
  ) {
    throw new Error(
      "Wallet returned an invalid GEN balance.",
    );
  }

  const balanceWei = BigInt(
    balanceRaw,
  );

  return {
    account: wallet.address,
    chainId: STUDIO_DEV_CHAIN_ID,
    balanceWei,
    balanceGen: formatGenAmount(
      balanceWei,
    ),
  };
}

export async function readMissionFundingSnapshot(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<MissionFundingSnapshot> {
  validateMissionIdentifier(
    missionId,
  );

  const raw = await wallet.client.readContract({
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName: "get_mission",
    args: [
      missionId,
    ],
    transactionHashVariant:
      TransactionHashVariant.LATEST_FINAL,
  });

  const record = valueRecord(
    raw,
    "get_mission",
  );

  const principal = valueString(
    record.principal,
    "Mission principal",
  );
  assertAddress(
    principal,
    "Mission principal",
  );

  return {
    missionId: valueString(
      record.mission_id,
      "Mission ID",
    ),
    principal,
    state: valueString(
      record.state,
      "Mission state",
    ),
    objective: valueString(
      record.objective,
      "Mission objective",
    ),
    budget: valueBigInt(
      record.budget,
      "Mission budget",
    ),
    fundedValue: valueBigInt(
      record.funded_value,
      "Mission funded value",
    ),
    preparedValue: valueBigInt(
      record.prepared_value,
      "Mission prepared value",
    ),
    effectCount: valueSafeNumber(
      record.effect_count,
      "Mission effect count",
    ),
    supplierCount: valueSafeNumber(
      record.supplier_count,
      "Mission supplier count",
    ),
    prepareDeadline: valueSafeNumber(
      record.prepare_deadline,
      "Mission preparation deadline",
    ),
    recoveryDeadline: valueSafeNumber(
      record.recovery_deadline,
      "Mission recovery deadline",
    ),
  };
}

export async function readSupplierAuthorization(
  wallet: ConnectedCommitWallet,
  missionId: string,
  supplier: string,
): Promise<boolean> {
  validateMissionIdentifier(
    missionId,
  );
  assertAddress(
    supplier,
    "Supplier",
  );

  const raw = await wallet.client.readContract({
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName: "is_supplier_authorized",
    args: [
      missionId,
      supplier,
    ],
    transactionHashVariant:
      TransactionHashVariant.LATEST_FINAL,
  });

  if (typeof raw !== "boolean") {
    throw new Error(
      "Supplier authorization read returned an unexpected value.",
    );
  }

  return raw;
}

export async function readMissionEffects(
  wallet: ConnectedCommitWallet,
  missionId: string,
  effectCount?: number,
): Promise<EffectSnapshot[]> {
  validateMissionIdentifier(
    missionId,
  );

  const count = effectCount
    ?? (
      await readMissionFundingSnapshot(
        wallet,
        missionId,
      )
    ).effectCount;

  if (
    !Number.isSafeInteger(count)
    || count < 0
    || count > 32
  ) {
    throw new Error(
      "Mission effect count is outside the supported contract bound.",
    );
  }

  const effects: EffectSnapshot[] = [];

  for (
    let index = 0;
    index < count;
    index += 1
  ) {
    const raw =
      await wallet.client.readContract({
        address:
          CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
        functionName:
          "get_effect_by_index",
        args: [
          missionId,
          index,
        ],
        transactionHashVariant:
          TransactionHashVariant.LATEST_FINAL,
      });

    const record = valueRecord(
      raw,
      "get_effect_by_index",
    );

    const supplier = valueString(
      record.supplier,
      "Effect supplier",
    );
    assertAddress(
      supplier,
      "Effect supplier",
    );

    const beneficiary = valueString(
      record.beneficiary,
      "Effect beneficiary",
    );
    assertAddress(
      beneficiary,
      "Effect beneficiary",
    );

    effects.push({
      missionId: valueString(
        record.mission_id,
        "Effect mission ID",
      ),
      effectId: valueString(
        record.effect_id,
        "Effect ID",
      ),
      supplier,
      digest: valueString(
        record.digest,
        "Effect digest",
      ),
      dependencyId: valueString(
        record.dependency_id,
        "Effect dependency ID",
      ),
      beneficiary,
      value: valueBigInt(
        record.value,
        "Effect value",
      ),
      expiry: valueSafeNumber(
        record.expiry,
        "Effect expiry",
      ),
    });
  }

  return effects;
}

function validateEffectId(
  effectId: string,
): string | null {
  if (
    effectId.length === 0
    || effectId.length > 512
    || effectId.includes(":")
    || [...effectId].some(
      (character) => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
      },
    )
  ) {
    return (
      "Effect ID must be printable ASCII, 1-512 characters, with no colon."
    );
  }

  return null;
}

function validateDependencyId(
  dependencyId: string,
): string | null {
  if (dependencyId.length === 0) {
    return null;
  }

  if (
    dependencyId.length > 512
    || !/^[A-Za-z0-9_-]+$/.test(
      dependencyId,
    )
  ) {
    return (
      "Dependency ID must use only letters, numbers, hyphen, and underscore."
    );
  }

  return null;
}

export function validateSupplierAuthorizationEligibility(
  mission: MissionFundingSnapshot,
  walletAddress: `0x${string}`,
  supplier: string,
  alreadyAuthorized: boolean,
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
      "Only the mission principal can authorize a supplier.",
    );
  }

  if (mission.state !== "PREPARING") {
    errors.push(
      "Mission must still be PREPARING to authorize a supplier.",
    );
  }

  if (nowSeconds > mission.prepareDeadline) {
    errors.push(
      "The mission preparation deadline has passed.",
    );
  }

  try {
    assertAddress(
      supplier,
      "Supplier",
    );
  } catch (error: unknown) {
    errors.push(
      error instanceof Error
        ? error.message
        : "Supplier address is invalid.",
    );
  }

  if (alreadyAuthorized) {
    errors.push(
      "Supplier is already authorized for this mission.",
    );
  }

  return errors;
}

export function validatePrepareEffectEligibility(
  mission: MissionFundingSnapshot,
  walletAddress: `0x${string}`,
  supplierAuthorized: boolean,
  effects: EffectSnapshot[],
  draft: PrepareEffectDraft,
  nowSeconds = Math.floor(
    Date.now() / 1000,
  ),
): string[] {
  const errors: string[] = [];

  if (mission.state !== "PREPARING") {
    errors.push(
      "Mission must still be PREPARING to prepare an effect.",
    );
  }

  if (nowSeconds > mission.prepareDeadline) {
    errors.push(
      "The mission preparation deadline has passed.",
    );
  }

  if (!supplierAuthorized) {
    errors.push(
      "Connected wallet is not an authorized supplier for this mission.",
    );
  }

  const effectIdError =
    validateEffectId(
      draft.effectId,
    );

  if (effectIdError !== null) {
    errors.push(
      effectIdError,
    );
  }

  if (
    !/^[0-9a-f]{64}$/.test(
      draft.effectDigest,
    )
  ) {
    errors.push(
      "Effect digest must be exactly 32-byte lowercase hex without 0x.",
    );
  }

  try {
    assertAddress(
      draft.beneficiary,
      "Effect beneficiary",
    );
  } catch (error: unknown) {
    errors.push(
      error instanceof Error
        ? error.message
        : "Effect beneficiary is invalid.",
    );
  }

  let value = ZERO_BIGINT;

  try {
    value = parseGenAmount(
      draft.valueGen,
    );
  } catch (error: unknown) {
    errors.push(
      error instanceof Error
        ? error.message
        : "Effect value is invalid.",
    );
  }

  if (
    mission.preparedValue + value
    > mission.budget
  ) {
    errors.push(
      "Prepared effects would exceed the mission budget.",
    );
  }

  if (
    !Number.isSafeInteger(
      draft.expiry,
    )
    || draft.expiry < mission.recoveryDeadline
  ) {
    errors.push(
      "Effect expiry must be at or after the mission recovery deadline.",
    );
  }

  if (
    effects.some(
      (effect) => (
        effect.effectId
        === draft.effectId
      ),
    )
  ) {
    errors.push(
      "Effect ID already exists on this mission.",
    );
  }

  if (effects.length >= 32) {
    errors.push(
      "Mission already reached the 32-effect contract limit.",
    );
  }

  const dependencyError =
    validateDependencyId(
      draft.dependencyId,
    );

  if (dependencyError !== null) {
    errors.push(
      dependencyError,
    );
  }

  if (
    draft.dependencyId.length > 0
    && draft.dependencyId
    === draft.effectId
  ) {
    errors.push(
      "Effect cannot depend on itself.",
    );
  }

  if (
    draft.dependencyId.length > 0
    && !effects.some(
      (effect) => (
        effect.effectId
        === draft.dependencyId
      ),
    )
  ) {
    errors.push(
      "Dependency effect does not exist on this mission.",
    );
  }

  return errors;
}

export async function quoteSupplierAuthorization(
  wallet: ConnectedCommitWallet,
  missionId: string,
  supplier: string,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const mission =
    await readMissionFundingSnapshot(
      wallet,
      missionId,
    );

  const alreadyAuthorized =
    await readSupplierAuthorization(
      wallet,
      missionId,
      supplier,
    );

  const errors =
    validateSupplierAuthorizationEligibility(
      mission,
      wallet.address,
      supplier,
      alreadyAuthorized,
    );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  assertAddress(
    supplier,
    "Supplier",
  );

  const call = {
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName:
      "authorize_supplier" as const,
    args: [
      missionId,
      supplier,
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
      "Wallet balance is insufficient for the quoted supplier-authorization fee deposit.",
    );
  }

  return {
    call,
    mission,
    supplier,
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

export async function submitSupplierAuthorization(
  wallet: ConnectedCommitWallet,
  quote: SupplierAuthorizationQuote,
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

export async function quotePrepareEffect(
  wallet: ConnectedCommitWallet,
  draft: PrepareEffectDraft,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const mission =
    await readMissionFundingSnapshot(
      wallet,
      draft.missionId,
    );

  const supplierAuthorized =
    await readSupplierAuthorization(
      wallet,
      draft.missionId,
      wallet.address,
    );

  const effects =
    await readMissionEffects(
      wallet,
      draft.missionId,
      mission.effectCount,
    );

  const errors =
    validatePrepareEffectEligibility(
      mission,
      wallet.address,
      supplierAuthorized,
      effects,
      draft,
    );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  assertAddress(
    draft.beneficiary,
    "Effect beneficiary",
  );

  const value = parseGenAmount(
    draft.valueGen,
  );

  const call = (
    draft.dependencyId.length > 0
      ? {
          address:
            CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
          functionName:
            "prepare_effect_with_dependency" as const,
          args: [
            draft.missionId,
            draft.effectId,
            draft.effectDigest,
            draft.beneficiary,
            value,
            BigInt(
              draft.expiry,
            ),
            draft.dependencyId,
          ],
        }
      : {
          address:
            CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
          functionName:
            "prepare_effect" as const,
          args: [
            draft.missionId,
            draft.effectId,
            draft.effectDigest,
            draft.beneficiary,
            value,
            BigInt(
              draft.expiry,
            ),
          ],
        }
  );

  const estimate =
    await wallet.client.estimateTransactionFeesForWrite({
      ...call,
    });

  if (
    preflight.balanceWei
    < estimate.feeValue
  ) {
    throw new Error(
      "Wallet balance is insufficient for the quoted effect-preparation fee deposit.",
    );
  }

  return {
    call,
    mission,
    existingEffects:
      effects,
    supplierAuthorized,
    preflight,
    value,
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

export async function submitPrepareEffect(
  wallet: ConnectedCommitWallet,
  quote: PrepareEffectQuote,
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

function validateKeyIdentifier(
  value: string,
  label: string,
  maxLength = 512,
): string | null {
  if (
    value.length === 0
    || value.length > maxLength
    || !/^[A-Za-z0-9_-]+$/.test(
      value,
    )
  ) {
    return (
      `${label} must use only letters, numbers, hyphen, and underscore.`
    );
  }

  return null;
}

function evidenceUrlIsWithinAuthority(
  url: string,
  authority: AuthoritySnapshot,
): boolean {
  if (
    url.length === 0
    || url.length > 2048
    || [...url].some(
      (character) => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
      },
    )
  ) {
    return false;
  }

  const origin =
    `https://${authority.host}`;

  if (!url.startsWith(
    origin,
  )) {
    return false;
  }

  const remainder =
    url.slice(
      origin.length,
    );

  if (
    !remainder.startsWith("/")
    || remainder.includes("?")
    || remainder.includes("#")
    || remainder.includes("%")
    || remainder.includes("\\")
  ) {
    return false;
  }

  if (remainder === "/") {
    return authority.pathPrefix === "/";
  }

  const segments =
    remainder.split("/");

  if (
    segments.slice(1).some(
      (segment) => (
        segment.length === 0
        || segment === "."
        || segment === ".."
      ),
    )
  ) {
    return false;
  }

  return (
    authority.pathPrefix === "/"
    || remainder === authority.pathPrefix
    || remainder.startsWith(
      `${authority.pathPrefix}/`,
    )
  );
}

export async function readMissionEvidenceContext(
  wallet: ConnectedCommitWallet,
  missionId: string,
): Promise<MissionEvidenceContext> {
  validateMissionIdentifier(
    missionId,
  );

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
    createdAt:
      valueSafeNumber(
        record.created_at,
        "Mission creation time",
      ),
  };
}

export async function readAuthority(
  wallet: ConnectedCommitWallet,
  authorityId: string,
): Promise<AuthoritySnapshot> {
  const authorityError =
    validateKeyIdentifier(
      authorityId,
      "Authority ID",
      64,
    );

  if (authorityError !== null) {
    throw new Error(
      authorityError,
    );
  }

  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_authority",
      args: [
        authorityId,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_authority",
    );

  const issuerAddress =
    valueString(
      record.issuer_address,
      "Authority issuer",
    );

  assertAddress(
    issuerAddress,
    "Authority issuer",
  );

  return {
    authorityId:
      valueString(
        record.authority_id,
        "Authority ID",
      ),
    active:
      valueBoolean(
        record.active,
        "Authority active flag",
      ),
    host:
      valueString(
        record.host,
        "Authority host",
      ),
    pathPrefix:
      valueString(
        record.path_prefix,
        "Authority path prefix",
      ),
    issuerAddress,
    authorityVersion:
      valueSafeNumber(
        record.authority_version,
        "Authority version",
      ),
  };
}

export async function readEvidenceAttestation(
  wallet: ConnectedCommitWallet,
  authorityId: string,
  recordId: string,
  recordVersion: number,
): Promise<EvidenceAttestationSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_evidence_attestation",
      args: [
        authorityId,
        recordId,
        recordVersion,
      ],
      transactionHashVariant:
        TransactionHashVariant.LATEST_FINAL,
    });

  const record =
    valueRecord(
      raw,
      "get_evidence_attestation",
    );

  const issuerAddress =
    valueString(
      record.issuer_address,
      "Attestation issuer",
    );

  assertAddress(
    issuerAddress,
    "Attestation issuer",
  );

  return {
    authorityId:
      valueString(
        record.authority_id,
        "Attestation authority ID",
      ),
    authorityVersion:
      valueSafeNumber(
        record.authority_version,
        "Attestation authority version",
      ),
    issuerAddress,
    recordId:
      valueString(
        record.record_id,
        "Attestation record ID",
      ),
    recordVersion:
      valueSafeNumber(
        record.record_version,
        "Attestation record version",
      ),
    missionId:
      valueString(
        record.mission_id,
        "Attestation mission ID",
      ),
    missionVersion:
      valueSafeNumber(
        record.mission_version,
        "Attestation mission version",
      ),
    url:
      valueString(
        record.url,
        "Attestation URL",
      ),
    recordHash:
      valueString(
        record.record_hash,
        "Attestation record hash",
      ),
    publishedAt:
      valueSafeNumber(
        record.published_at,
        "Attestation publication time",
      ),
    expiresAt:
      valueSafeNumber(
        record.expires_at,
        "Attestation expiry time",
      ),
  };
}

export async function readEvidence(
  wallet: ConnectedCommitWallet,
  missionId: string,
  evidenceId: string,
): Promise<EvidenceSnapshot> {
  const raw =
    await wallet.client.readContract({
      address:
        CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
      functionName:
        "get_evidence",
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
      "get_evidence",
    );

  const issuerAddress =
    valueString(
      record.issuer_address,
      "Evidence issuer",
    );

  assertAddress(
    issuerAddress,
    "Evidence issuer",
  );

  return {
    missionId:
      valueString(
        record.mission_id,
        "Evidence mission ID",
      ),
    evidenceId:
      valueString(
        record.evidence_id,
        "Evidence ID",
      ),
    authorityId:
      valueString(
        record.authority_id,
        "Evidence authority ID",
      ),
    authorityVersion:
      valueSafeNumber(
        record.authority_version,
        "Evidence authority version",
      ),
    issuerAddress,
    recordId:
      valueString(
        record.record_id,
        "Evidence record ID",
      ),
    recordVersion:
      valueSafeNumber(
        record.record_version,
        "Evidence record version",
      ),
    missionVersion:
      valueSafeNumber(
        record.mission_version,
        "Evidence mission version",
      ),
    url:
      valueString(
        record.url,
        "Evidence URL",
      ),
    recordHash:
      valueString(
        record.record_hash,
        "Evidence record hash",
      ),
    subject:
      valueString(
        record.subject,
        "Evidence subject",
      ),
    publishedAt:
      valueSafeNumber(
        record.published_at,
        "Evidence publication time",
      ),
    expiresAt:
      valueSafeNumber(
        record.expires_at,
        "Evidence expiry time",
      ),
  };
}

export async function readMissionEvidence(
  wallet: ConnectedCommitWallet,
  missionId: string,
  evidenceCount?: number,
): Promise<EvidenceSnapshot[]> {
  const count =
    evidenceCount
    ?? (
      await readMissionEvidenceContext(
        wallet,
        missionId,
      )
    ).evidenceCount;

  if (
    !Number.isSafeInteger(
      count,
    )
    || count < 0
    || count > 16
  ) {
    throw new Error(
      "Mission evidence count is outside the 16-record contract bound.",
    );
  }

  const evidence: EvidenceSnapshot[] = [];

  for (
    let index = 0;
    index < count;
    index += 1
  ) {
    const raw =
      await wallet.client.readContract({
        address:
          CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
        functionName:
          "get_evidence_by_index",
        args: [
          missionId,
          index,
        ],
        transactionHashVariant:
          TransactionHashVariant.LATEST_FINAL,
      });

    const record =
      valueRecord(
        raw,
        "get_evidence_by_index",
      );

    const issuerAddress =
      valueString(
        record.issuer_address,
        "Evidence issuer",
      );

    assertAddress(
      issuerAddress,
      "Evidence issuer",
    );

    evidence.push({
      missionId:
        valueString(
          record.mission_id,
          "Evidence mission ID",
        ),
      evidenceId:
        valueString(
          record.evidence_id,
          "Evidence ID",
        ),
      authorityId:
        valueString(
          record.authority_id,
          "Evidence authority ID",
        ),
      authorityVersion:
        valueSafeNumber(
          record.authority_version,
          "Evidence authority version",
        ),
      issuerAddress,
      recordId:
        valueString(
          record.record_id,
          "Evidence record ID",
        ),
      recordVersion:
        valueSafeNumber(
          record.record_version,
          "Evidence record version",
        ),
      missionVersion:
        valueSafeNumber(
          record.mission_version,
          "Evidence mission version",
        ),
      url:
        valueString(
          record.url,
          "Evidence URL",
        ),
      recordHash:
        valueString(
          record.record_hash,
          "Evidence record hash",
        ),
      subject:
        valueString(
          record.subject,
          "Evidence subject",
        ),
      publishedAt:
        valueSafeNumber(
          record.published_at,
          "Evidence publication time",
        ),
      expiresAt:
        valueSafeNumber(
          record.expires_at,
          "Evidence expiry time",
        ),
    });
  }

  return evidence;
}

export function validateEvidenceAttestationEligibility(
  mission: MissionEvidenceContext,
  authority: AuthoritySnapshot,
  walletAddress: `0x${string}`,
  draft: AttestEvidenceDraft,
): string[] {
  const errors: string[] = [];

  if (!authority.active) {
    errors.push(
      "Authority is inactive.",
    );
  }

  if (
    authority.issuerAddress.toLowerCase()
    !== walletAddress.toLowerCase()
  ) {
    errors.push(
      "Connected wallet is not the registered authority issuer.",
    );
  }

  const authorityError =
    validateKeyIdentifier(
      draft.authorityId,
      "Authority ID",
      64,
    );

  if (authorityError !== null) {
    errors.push(
      authorityError,
    );
  }

  const recordError =
    validateKeyIdentifier(
      draft.recordId,
      "Record ID",
    );

  if (recordError !== null) {
    errors.push(
      recordError,
    );
  }

  if (
    !Number.isSafeInteger(
      draft.recordVersion,
    )
    || draft.recordVersion <= 0
  ) {
    errors.push(
      "Record version must be a positive integer.",
    );
  }

  if (
    draft.missionId
    !== mission.missionId
  ) {
    errors.push(
      "Attestation mission does not match the finalized mission read.",
    );
  }

  if (
    draft.authorityId
    !== authority.authorityId
  ) {
    errors.push(
      "Attestation authority does not match the finalized authority read.",
    );
  }

  if (
    !evidenceUrlIsWithinAuthority(
      draft.url,
      authority,
    )
  ) {
    errors.push(
      "Evidence URL is outside the registered authority origin/path.",
    );
  }

  if (
    !/^[0-9a-f]{64}$/.test(
      draft.recordHash,
    )
  ) {
    errors.push(
      "Record hash must be exactly 32-byte lowercase hex without 0x.",
    );
  }

  if (
    !Number.isSafeInteger(
      draft.publishedAt,
    )
    || draft.publishedAt <= 0
  ) {
    errors.push(
      "Published timestamp must be a positive Unix timestamp.",
    );
  } else if (
    draft.publishedAt
    < mission.createdAt
  ) {
    errors.push(
      "Evidence cannot be published before the mission was created.",
    );
  }

  if (
    !Number.isSafeInteger(
      draft.expiresAt,
    )
    || draft.expiresAt <= 0
  ) {
    errors.push(
      "Expiry timestamp must be a positive Unix timestamp.",
    );
  } else if (
    draft.expiresAt
    < mission.recoveryDeadline
  ) {
    errors.push(
      "Evidence expiry must be at or after the mission recovery deadline.",
    );
  }

  return errors;
}

export function validateEvidenceRegistrationEligibility(
  mission: MissionEvidenceContext,
  walletAddress: `0x${string}`,
  attestation: EvidenceAttestationSnapshot,
  existingEvidence: EvidenceSnapshot[],
  draft: RegisterEvidenceDraft,
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
      "Only the mission principal can register evidence.",
    );
  }

  if (
    mission.state
    !== "PREPARING"
  ) {
    errors.push(
      "Mission must still be PREPARING to register evidence.",
    );
  }

  if (
    nowSeconds
    > mission.prepareDeadline
  ) {
    errors.push(
      "The mission preparation deadline has passed.",
    );
  }

  const evidenceError =
    validateKeyIdentifier(
      draft.evidenceId,
      "Evidence ID",
    );

  if (evidenceError !== null) {
    errors.push(
      evidenceError,
    );
  }

  if (
    existingEvidence.some(
      (item) => (
        item.evidenceId
        === draft.evidenceId
      ),
    )
  ) {
    errors.push(
      "Evidence ID already exists on this mission.",
    );
  }

  if (
    existingEvidence.length >= 16
  ) {
    errors.push(
      "Mission already reached the 16-evidence contract limit.",
    );
  }

  if (
    attestation.authorityId
    !== draft.authorityId
    || attestation.recordId
    !== draft.recordId
    || attestation.recordVersion
    !== draft.recordVersion
  ) {
    errors.push(
      "Selected attestation identity does not match the registration request.",
    );
  }

  if (
    attestation.missionId
    !== mission.missionId
  ) {
    errors.push(
      "Attestation is bound to a different mission.",
    );
  }

  if (
    attestation.missionVersion
    !== mission.version
  ) {
    errors.push(
      "Attestation mission version does not match the finalized mission version.",
    );
  }

  return errors;
}

export async function quoteAttestEvidence(
  wallet: ConnectedCommitWallet,
  draft: AttestEvidenceDraft,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const mission =
    await readMissionEvidenceContext(
      wallet,
      draft.missionId,
    );

  const authority =
    await readAuthority(
      wallet,
      draft.authorityId,
    );

  const errors =
    validateEvidenceAttestationEligibility(
      mission,
      authority,
      wallet.address,
      draft,
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
      "attest_evidence" as const,
    args: [
      authority.authorityId,
      authority.authorityVersion,
      draft.recordId,
      draft.recordVersion,
      mission.missionId,
      mission.version,
      draft.url,
      draft.recordHash,
      draft.publishedAt,
      draft.expiresAt,
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
      "Wallet balance is insufficient for the quoted evidence-attestation fee deposit.",
    );
  }

  return {
    call,
    mission,
    authority,
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

export async function submitEvidenceAttestation(
  wallet: ConnectedCommitWallet,
  quote: AttestEvidenceQuote,
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

export async function quoteRegisterEvidence(
  wallet: ConnectedCommitWallet,
  draft: RegisterEvidenceDraft,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const mission =
    await readMissionEvidenceContext(
      wallet,
      draft.missionId,
    );

  const attestation =
    await readEvidenceAttestation(
      wallet,
      draft.authorityId,
      draft.recordId,
      draft.recordVersion,
    );

  const existingEvidence =
    await readMissionEvidence(
      wallet,
      draft.missionId,
      mission.evidenceCount,
    );

  const errors =
    validateEvidenceRegistrationEligibility(
      mission,
      wallet.address,
      attestation,
      existingEvidence,
      draft,
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
      "register_evidence" as const,
    args: [
      draft.missionId,
      draft.evidenceId,
      attestation.authorityId,
      attestation.authorityVersion,
      attestation.recordId,
      attestation.recordVersion,
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
      "Wallet balance is insufficient for the quoted evidence-registration fee deposit.",
    );
  }

  return {
    call,
    mission,
    attestation,
    existingEvidence,
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

export async function submitEvidenceRegistration(
  wallet: ConnectedCommitWallet,
  quote: RegisterEvidenceQuote,
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

export function validateFundingEligibility(
  mission: MissionFundingSnapshot,
  walletAddress: `0x${string}`,
  amount: bigint,
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
      "Only the mission principal can fund this mission.",
    );
  }

  if (mission.state !== "PREPARING") {
    errors.push(
      "Mission must still be PREPARING to accept funding.",
    );
  }

  if (nowSeconds > mission.prepareDeadline) {
    errors.push(
      "The mission preparation deadline has passed.",
    );
  }

  if (amount <= ZERO_BIGINT) {
    errors.push(
      "Funding value must be greater than zero.",
    );
  }

  if (
    mission.fundedValue + amount
    > mission.budget
  ) {
    errors.push(
      "Funding would exceed the mission budget.",
    );
  }

  return errors;
}

export async function quoteFundMission(
  wallet: ConnectedCommitWallet,
  missionId: string,
  amountGen: string,
) {
  const preflight =
    await preflightCommitWallet(
      wallet,
    );

  const mission =
    await readMissionFundingSnapshot(
      wallet,
      missionId,
    );

  const amount = parseGenAmount(
    amountGen,
  );

  const errors =
    validateFundingEligibility(
      mission,
      wallet.address,
      amount,
    );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  const call = {
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName: "fund_mission" as const,
    args: [
      missionId,
    ],
    value: amount,
  };

  const estimate =
    await wallet.client.estimateTransactionFeesForWrite({
      ...call,
    });

  const requiredBalance =
    amount + estimate.feeValue;

  if (
    preflight.balanceWei
    < requiredBalance
  ) {
    throw new Error(
      "Wallet balance is insufficient for the funding value plus the quoted fee deposit.",
    );
  }

  return {
    call,
    mission,
    amount,
    preflight,
    feeValue: estimate.feeValue,
    requiredBalance,
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

function buildCreateMissionCall(
  draft: MissionDraft,
) {
  const errors = validateMissionDraft(
    draft,
  );

  if (errors.length > 0) {
    throw new Error(
      errors.join(" "),
    );
  }

  assertAddress(
    CURRENT_DEPLOYMENT_ANCHOR.contractAddress,
    "COMMIT coordinator",
  );

  return {
    address:
      CURRENT_DEPLOYMENT_ANCHOR.contractAddress as `0x${string}`,
    functionName: "create_mission" as const,
    args: [
      draft.missionId,
      draft.objective,
      COMMIT_POLICY_DIGEST,
      parseGenAmount(
        draft.budgetGen,
      ),
      draft.refundBeneficiary,
      BigInt(
        draft.prepareDeadline,
      ),
      BigInt(
        draft.recoveryDeadline,
      ),
    ],
  };
}

export async function quoteCreateMission(
  wallet: ConnectedCommitWallet,
  draft: MissionDraft,
) {
  const call = buildCreateMissionCall(
    draft,
  );

  const estimate =
    await wallet.client.estimateTransactionFeesForWrite({
      ...call,
    });

  return {
    call,
    feeValue: estimate.feeValue,
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

function assertTransactionHash(
  value: string,
): asserts value is TransactionHash {
  if (!/^0x[0-9a-fA-F]{64}$/.test(value)) {
    throw new Error(
      "GenLayer returned a malformed transaction hash.",
    );
  }
}

export async function submitCreateMission(
  wallet: ConnectedCommitWallet,
  quote: CreateMissionQuote,
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

export async function submitFundMission(
  wallet: ConnectedCommitWallet,
  quote: FundMissionQuote,
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

export async function trackCommitTransaction(
  txId: TransactionHash,
  onProgress: (
    progress: TransactionProgress,
  ) => void,
) {
  const readClient = createClient({
    chain: studioDevnet,
  });

  onProgress({
    phase: "submitted",
    txId,
  });

  const accepted =
    await readClient.waitForTransactionReceipt({
      hash: txId,
      status: TransactionStatus.ACCEPTED,
      fullTransaction: false,
    });

  onProgress({
    phase: "accepted",
    txId,
    statusName: receiptText(
      accepted,
      "statusName",
    ),
    executionResultName: receiptText(
      accepted,
      "txExecutionResultName",
    ),
  });

  const finalized =
    await readClient.waitForFinalization({
      hash: txId,
    });

  const executionResultName =
    receiptText(
      finalized,
      "txExecutionResultName",
    );

  const successful =
    executionResultName
    === ExecutionResult.FINISHED_WITH_RETURN;

  onProgress({
    phase: "finalized",
    txId,
    statusName: receiptText(
      finalized,
      "statusName",
    ),
    executionResultName,
    successful,
  });

  return {
    finalized,
    successful,
  };
}
