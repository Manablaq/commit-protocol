import {
  describe,
  expect,
  it,
} from "vitest";
import {
  COMMIT_POLICY_DIGEST,
  formatGenAmount,
  parseGenAmount,
  preflightCommitWallet,
  STUDIO_DEV_CHAIN_ID,
  validateFundingEligibility,
  validateEvidenceAttestationEligibility,
  validateEvidenceRegistrationEligibility,
  validateMissionDraft,
  validatePrepareEffectEligibility,
  validateSupplierAuthorizationEligibility,
  type AuthoritySnapshot,
  type ConnectedCommitWallet,
  type EffectSnapshot,
  type EvidenceAttestationSnapshot,
  type EvidenceSnapshot,
  type MissionEvidenceContext,
  type MissionFundingSnapshot,
} from "@/lib/genlayer-browser";

describe("COMMIT GenLayer browser integration", () => {
  it("binds the deployed policy and Studio Next chain", () => {
    expect(STUDIO_DEV_CHAIN_ID).toBe(61997);
    expect(COMMIT_POLICY_DIGEST).toBe(
      "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103",
    );
  });

  it("converts GEN to exact 18-decimal base units", () => {
    expect(parseGenAmount("1")).toBe(
      BigInt("1000000000000000000"),
    );
    expect(parseGenAmount("1.25")).toBe(
      BigInt("1250000000000000000"),
    );
    expect(formatGenAmount(
      BigInt("1250000000000000000"),
    )).toBe("1.25");
  });

  it("rejects invalid mission identifiers and deadline order", () => {
    const now = Math.floor(Date.now() / 1000);

    const errors = validateMissionDraft({
      missionId: "bad:id",
      objective: "Objective",
      budgetGen: "1",
      refundBeneficiary:
        "0x1111111111111111111111111111111111111111",
      prepareDeadline: now + 3600,
      recoveryDeadline: now + 1800,
    });

    expect(errors.join(" ")).toContain("no colon");
    expect(errors.join(" ")).toContain(
      "Recovery deadline",
    );
  });

  it("rejects funding from a non-principal or above remaining budget", () => {
    const principal =
      "0x1111111111111111111111111111111111111111" as const;

    const mission: MissionFundingSnapshot = {
      missionId: "mission-1",
      principal,
      state: "PREPARING",
      objective: "Objective",
      budget: BigInt("1000000000000000000"),
      fundedValue: BigInt("750000000000000000"),
      preparedValue: BigInt(0),
      effectCount: 0,
      supplierCount: 1,
      prepareDeadline: 2_000_000_000,
      recoveryDeadline: 2_000_100_000,
    };

    const wrongPrincipal =
      validateFundingEligibility(
        mission,
        "0x2222222222222222222222222222222222222222",
        BigInt("100000000000000000"),
        1_900_000_000,
      );

    expect(
      wrongPrincipal.join(" "),
    ).toContain(
      "Only the mission principal",
    );

    const overBudget =
      validateFundingEligibility(
        mission,
        principal,
        BigInt("300000000000000000"),
        1_900_000_000,
      );

    expect(
      overBudget.join(" "),
    ).toContain(
      "exceed the mission budget",
    );
  });

  it("preflights the exact Studio Next account and balance", async () => {
    const address =
      "0x1111111111111111111111111111111111111111" as const;

    const wallet = {
      address,
      provider: {
        request: async ({
          method,
        }: {
          method: string;
        }) => {
          if (method === "eth_chainId") {
            return "0xf22d";
          }

          if (method === "eth_accounts") {
            return [address];
          }

          if (method === "eth_getBalance") {
            return "0xde0b6b3a7640000";
          }

          throw new Error(
            `Unexpected method: ${method}`,
          );
        },
      },
      client: {} as ConnectedCommitWallet["client"],
    } as ConnectedCommitWallet;

    const result =
      await preflightCommitWallet(
        wallet,
      );

    expect(result.chainId).toBe(61997);
    expect(result.account).toBe(address);
    expect(result.balanceGen).toBe("1");
  });

  it("enforces principal-only supplier authorization", () => {
    const mission: MissionFundingSnapshot = {
      missionId: "mission-1",
      principal:
        "0x1111111111111111111111111111111111111111",
      state: "PREPARING",
      objective: "Objective",
      budget: BigInt("1000000000000000000"),
      fundedValue: BigInt("1000000000000000000"),
      preparedValue: BigInt(0),
      effectCount: 0,
      supplierCount: 1,
      prepareDeadline: 2_000_000_000,
      recoveryDeadline: 2_000_100_000,
    };

    const errors =
      validateSupplierAuthorizationEligibility(
        mission,
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333",
        false,
        1_900_000_000,
      );

    expect(
      errors.join(" "),
    ).toContain(
      "Only the mission principal",
    );
  });

  it("enforces supplier, budget, expiry, uniqueness, and dependency constraints", () => {
    const mission: MissionFundingSnapshot = {
      missionId: "mission-1",
      principal:
        "0x1111111111111111111111111111111111111111",
      state: "PREPARING",
      objective: "Objective",
      budget: BigInt("1000000000000000000"),
      fundedValue: BigInt("1000000000000000000"),
      preparedValue: BigInt("800000000000000000"),
      effectCount: 1,
      supplierCount: 1,
      prepareDeadline: 2_000_000_000,
      recoveryDeadline: 2_000_100_000,
    };

    const existing: EffectSnapshot[] = [
      {
        missionId: "mission-1",
        effectId: "existing-effect",
        supplier:
          "0x1111111111111111111111111111111111111111",
        digest: "a".repeat(64),
        dependencyId: "",
        beneficiary:
          "0x4444444444444444444444444444444444444444",
        value: BigInt("100000000000000000"),
        expiry: 2_000_200_000,
      },
    ];

    const errors =
      validatePrepareEffectEligibility(
        mission,
        "0x1111111111111111111111111111111111111111",
        false,
        existing,
        {
          missionId: "mission-1",
          effectId: "existing-effect",
          effectDigest: "A".repeat(64),
          beneficiary:
            "0x4444444444444444444444444444444444444444",
          valueGen: "0.3",
          expiry: 2_000_000_001,
          dependencyId: "missing-effect",
        },
        1_900_000_000,
      );

    const joined =
      errors.join(" ");

    expect(joined).toContain(
      "not an authorized supplier",
    );
    expect(joined).toContain(
      "lowercase hex",
    );
    expect(joined).toContain(
      "exceed the mission budget",
    );
    expect(joined).toContain(
      "at or after the mission recovery deadline",
    );
    expect(joined).toContain(
      "already exists",
    );
    expect(joined).toContain(
      "Dependency effect does not exist",
    );
  });


  it("enforces issuer identity authority scope and evidence freshness", () => {
    const mission: MissionEvidenceContext = {
      missionId: "mission-1",
      principal:
        "0x1111111111111111111111111111111111111111",
      state: "PREPARING",
      version: 1,
      evidenceCount: 0,
      prepareDeadline: 2_000_000_000,
      recoveryDeadline: 2_000_100_000,
      createdAt: 1_900_000_000,
    };

    const authority: AuthoritySnapshot = {
      authorityId: "authority-a",
      active: true,
      host: "evidence.example",
      pathPrefix: "/records",
      issuerAddress:
        "0x2222222222222222222222222222222222222222",
      authorityVersion: 3,
    };

    const errors =
      validateEvidenceAttestationEligibility(
        mission,
        authority,
        "0x3333333333333333333333333333333333333333",
        {
          missionId: "mission-1",
          authorityId: "authority-a",
          recordId: "record-1",
          recordVersion: 1,
          url:
            "https://evil.example/records/record-1.json",
          recordHash: "A".repeat(64),
          publishedAt: 1_800_000_000,
          expiresAt: 2_000_000_001,
        },
      );

    const joined =
      errors.join(" ");

    expect(joined).toContain(
      "not the registered authority issuer",
    );
    expect(joined).toContain(
      "outside the registered authority origin/path",
    );
    expect(joined).toContain(
      "lowercase hex",
    );
    expect(joined).toContain(
      "before the mission was created",
    );
    expect(joined).toContain(
      "at or after the mission recovery deadline",
    );
  });

  it("enforces principal registration against exact finalized attestation identity", () => {
    const mission: MissionEvidenceContext = {
      missionId: "mission-1",
      principal:
        "0x1111111111111111111111111111111111111111",
      state: "PREPARING",
      version: 2,
      evidenceCount: 1,
      prepareDeadline: 2_000_000_000,
      recoveryDeadline: 2_000_100_000,
      createdAt: 1_900_000_000,
    };

    const attestation: EvidenceAttestationSnapshot = {
      authorityId: "authority-a",
      authorityVersion: 3,
      issuerAddress:
        "0x2222222222222222222222222222222222222222",
      recordId: "record-1",
      recordVersion: 4,
      missionId: "mission-other",
      missionVersion: 1,
      url:
        "https://evidence.example/records/record-1.json",
      recordHash: "a".repeat(64),
      publishedAt: 1_900_000_100,
      expiresAt: 2_000_200_000,
    };

    const existing: EvidenceSnapshot[] = [
      {
        missionId: "mission-1",
        evidenceId: "evidence-primary",
        authorityId: "authority-b",
        authorityVersion: 1,
        issuerAddress:
          "0x4444444444444444444444444444444444444444",
        recordId: "record-b",
        recordVersion: 1,
        missionVersion: 2,
        url:
          "https://other.example/evidence.json",
        recordHash: "b".repeat(64),
        subject: "mission-1",
        publishedAt: 1_900_000_100,
        expiresAt: 2_000_200_000,
      },
    ];

    const errors =
      validateEvidenceRegistrationEligibility(
        mission,
        "0x3333333333333333333333333333333333333333",
        attestation,
        existing,
        {
          missionId: "mission-1",
          evidenceId: "evidence-primary",
          authorityId: "authority-a",
          recordId: "record-1",
          recordVersion: 4,
        },
        1_950_000_000,
      );

    const joined =
      errors.join(" ");

    expect(joined).toContain(
      "Only the mission principal",
    );
    expect(joined).toContain(
      "already exists",
    );
    expect(joined).toContain(
      "bound to a different mission",
    );
    expect(joined).toContain(
      "mission version does not match",
    );
  });

});
