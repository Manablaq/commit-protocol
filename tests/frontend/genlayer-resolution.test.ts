import {
  describe,
  expect,
  it,
} from "vitest";
import {
  validateEvaluateEligibility,
  validateExpireEligibility,
  validateRepairEligibility,
  type EvidenceFailureSnapshot,
  type ResolutionMissionSnapshot,
} from "@/lib/genlayer-resolution";
import {
  type EvidenceAttestationSnapshot,
  type EvidenceSnapshot,
} from "@/lib/genlayer-browser";

const PRINCIPAL =
  "0x1111111111111111111111111111111111111111" as const;
const ISSUER =
  "0x2222222222222222222222222222222222222222" as const;

function mission(
  overrides: Partial<ResolutionMissionSnapshot> = {},
): ResolutionMissionSnapshot {
  return {
    missionId:
      "mission-1",
    principal:
      PRINCIPAL,
    state:
      "SEALED",
    version:
      1,
    decision:
      "",
    reasonCode:
      "",
    decisionNonce:
      "",
    effectRoot:
      "a".repeat(64),
    evidenceRoot:
      "b".repeat(64),
    evaluationEvidenceRoot:
      "",
    allocationApplied:
      false,
    refundBeneficiary:
      PRINCIPAL,
    refundEntitlement:
      BigInt(0),
    evaluationCount:
      0,
    evidenceCount:
      2,
    recoveryDeadline:
      2_000_000_000,
    ...overrides,
  };
}

const evidence: EvidenceSnapshot = {
  missionId:
    "mission-1",
  evidenceId:
    "evidence-a",
  authorityId:
    "authority-a",
  authorityVersion:
    2,
  issuerAddress:
    ISSUER,
  recordId:
    "record-a",
  recordVersion:
    1,
  missionVersion:
    1,
  url:
    "https://evidence.example/records/a.json",
  recordHash:
    "c".repeat(64),
  subject:
    "mission-1",
  publishedAt:
    1_900_000_000,
  expiresAt:
    2_100_000_000,
};

const failure: EvidenceFailureSnapshot = {
  status:
    "REPAIR_REQUIRED",
  failureCode:
    "payload_hash_mismatch",
  evidenceId:
    "evidence-a",
  recordId:
    "record-a",
  failedRecordVersion:
    1,
  missionVersion:
    1,
  attempt:
    1,
};

const repairAttestation: EvidenceAttestationSnapshot = {
  authorityId:
    "authority-a",
  authorityVersion:
    2,
  issuerAddress:
    ISSUER,
  recordId:
    "record-a",
  recordVersion:
    2,
  missionId:
    "mission-1",
  missionVersion:
    1,
  url:
    "https://evidence.example/records/a-v2.json",
  recordHash:
    "d".repeat(64),
  publishedAt:
    1_900_000_100,
  expiresAt:
    2_100_000_000,
};

describe(
  "resolution safety",
  () => {
    it(
      "allows permissionless evaluation only while sealed and before recovery",
      () => {
        expect(
          validateEvaluateEligibility(
            mission(),
            1_950_000_000,
          ),
        ).toEqual([]);

        expect(
          validateEvaluateEligibility(
            mission({
              state:
                "COMMITTED",
              decision:
                "COMMIT",
            }),
            1_950_000_000,
          ).join(" "),
        ).toContain(
          "SEALED",
        );
      },
    );

    it(
      "binds repair to principal identity and a strictly newer attested record",
      () => {
        expect(
          validateRepairEligibility(
            mission(),
            PRINCIPAL,
            evidence,
            failure,
            repairAttestation,
            2,
            1_950_000_000,
          ),
        ).toEqual([]);

        const errors =
          validateRepairEligibility(
            mission(),
            "0x9999999999999999999999999999999999999999",
            evidence,
            failure,
            {
              ...repairAttestation,
              issuerAddress:
                "0x3333333333333333333333333333333333333333",
            },
            1,
            1_950_000_000,
          ).join(" ");

        expect(errors).toContain(
          "Only the mission principal",
        );
        expect(errors).toContain(
          "newer than the failed active record version",
        );
        expect(errors).toContain(
          "issuer does not match",
        );
      },
    );

    it(
      "permits deadline recovery only for recoverable nonterminal states after the deadline",
      () => {
        expect(
          validateExpireEligibility(
            mission({
              state:
                "DECISION_PENDING",
            }),
            2_000_000_000,
          ),
        ).toEqual([]);

        expect(
          validateExpireEligibility(
            mission(),
            1_999_999_999,
          ).join(" "),
        ).toContain(
          "Recovery deadline has not passed",
        );

        expect(
          validateExpireEligibility(
            mission({
              state:
                "COMMITTED",
            }),
            2_000_000_000,
          ).join(" "),
        ).toContain(
          "already terminal",
        );
      },
    );
  },
);
