import {
  describe,
  expect,
  it,
} from "vitest";
import {
  validateClaimEligibility,
  type ClaimSnapshot,
} from "@/lib/genlayer-claim";

const BENEFICIARY =
  "0x1111111111111111111111111111111111111111" as const;

function snapshot(
  overrides: Partial<ClaimSnapshot> = {},
): ClaimSnapshot {
  return {
    mission: {
      missionId:
        "mission-1",
      principal:
        "0x2222222222222222222222222222222222222222",
      state:
        "COMMITTED",
      version:
        1,
      decision:
        "COMMIT",
      reasonCode:
        "all_sources_and_effects_eligible",
      decisionNonce:
        "a".repeat(64),
      effectRoot:
        "b".repeat(64),
      evidenceRoot:
        "c".repeat(64),
      evaluationEvidenceRoot:
        "d".repeat(64),
      allocationApplied:
        true,
      refundBeneficiary:
        "0x3333333333333333333333333333333333333333",
      refundEntitlement:
        BigInt(0),
      evaluationCount:
        1,
      evidenceCount:
        2,
      recoveryDeadline:
        2_000_000_000,
    },
    receipt: {
      missionId:
        "mission-1",
      state:
        "COMMITTED",
      decision:
        "COMMIT",
      reasonCode:
        "all_sources_and_effects_eligible",
      allocationApplied:
        true,
      refundBeneficiary:
        "0x3333333333333333333333333333333333333333",
      refundEntitlement:
        BigInt(0),
      externalWithdrawalRecovery:
        false,
    },
    beneficiary:
      BENEFICIARY,
    missionClaimable:
      BigInt("500000000000000000"),
    aggregateClaimable:
      BigInt("750000000000000000"),
    withdrawalCount:
      7,
    ...overrides,
  };
}

describe(
  "beneficiary claim safety",
  () => {
    it(
      "accepts a positive terminal finalized entitlement",
      () => {
        expect(
          validateClaimEligibility(
            snapshot(),
          ),
        ).toEqual([]);
      },
    );

    it(
      "rejects nonterminal or unapplied allocation state",
      () => {
        const errors =
          validateClaimEligibility(
            snapshot({
              mission: {
                ...snapshot().mission,
                state:
                  "DECISION_PENDING",
                allocationApplied:
                  false,
              },
              receipt: {
                ...snapshot().receipt,
                state:
                  "DECISION_PENDING",
                allocationApplied:
                  false,
              },
            }),
          ).join(" ");

        expect(errors).toContain(
          "COMMITTED or ABORTED",
        );
        expect(errors).toContain(
          "allocation has not been applied",
        );
      },
    );

    it(
      "rejects zero entitlement and inconsistent aggregate accounting",
      () => {
        const errors =
          validateClaimEligibility(
            snapshot({
              missionClaimable:
                BigInt("500000000000000000"),
              aggregateClaimable:
                BigInt("100000000000000000"),
            }),
          ).join(" ");

        expect(errors).toContain(
          "Aggregate claimable balance is below",
        );

        expect(
          validateClaimEligibility(
            snapshot({
              missionClaimable:
                BigInt(0),
            }),
          ).join(" "),
        ).toContain(
          "no claimable balance",
        );
      },
    );

    it(
      "rejects unexpected external withdrawal recovery mode",
      () => {
        expect(
          validateClaimEligibility(
            snapshot({
              receipt: {
                ...snapshot().receipt,
                externalWithdrawalRecovery:
                  true,
              },
            }),
          ).join(" "),
        ).toContain(
          "Unexpected external withdrawal recovery mode",
        );
      },
    );
  },
);
