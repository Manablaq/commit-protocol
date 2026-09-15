import {
  describe,
  expect,
  it,
} from "vitest";
import {
  validateEffectGraph,
  validateSealMissionEligibility,
  type IndependentEvidencePair,
  type SealMissionSnapshot,
} from "@/lib/genlayer-seal";
import {
  type EffectSnapshot,
  type EvidenceSnapshot,
} from "@/lib/genlayer-browser";

const WALLET =
  "0x1111111111111111111111111111111111111111" as const;

function mission(
  overrides: Partial<SealMissionSnapshot> = {},
): SealMissionSnapshot {
  return {
    missionId:
      "mission-1",
    principal:
      WALLET,
    state:
      "PREPARING",
    version:
      1,
    effectRoot:
      "",
    evidenceRoot:
      "",
    budget:
      BigInt("1000000000000000000"),
    fundedValue:
      BigInt("1000000000000000000"),
    preparedValue:
      BigInt("500000000000000000"),
    effectCount:
      2,
    evidenceCount:
      2,
    prepareDeadline:
      2_000_000_000,
    recoveryDeadline:
      2_000_100_000,
    ...overrides,
  };
}

const effects: EffectSnapshot[] = [
  {
    missionId:
      "mission-1",
    effectId:
      "effect-a",
    supplier:
      WALLET,
    digest:
      "a".repeat(64),
    dependencyId:
      "",
    beneficiary:
      "0x2222222222222222222222222222222222222222",
    value:
      BigInt("250000000000000000"),
    expiry:
      2_000_200_000,
  },
  {
    missionId:
      "mission-1",
    effectId:
      "effect-b",
    supplier:
      WALLET,
    digest:
      "b".repeat(64),
    dependencyId:
      "effect-a",
    beneficiary:
      "0x3333333333333333333333333333333333333333",
    value:
      BigInt("250000000000000000"),
    expiry:
      2_000_200_000,
  },
];

const evidence: EvidenceSnapshot[] = [
  {
    missionId:
      "mission-1",
    evidenceId:
      "evidence-a",
    authorityId:
      "authority-a",
    authorityVersion:
      1,
    issuerAddress:
      "0x4444444444444444444444444444444444444444",
    recordId:
      "record-a",
    recordVersion:
      1,
    missionVersion:
      1,
    url:
      "https://a.example/records/a.json",
    recordHash:
      "c".repeat(64),
    subject:
      "mission-1",
    publishedAt:
      1_900_000_000,
    expiresAt:
      2_000_200_000,
  },
  {
    missionId:
      "mission-1",
    evidenceId:
      "evidence-b",
    authorityId:
      "authority-b",
    authorityVersion:
      1,
    issuerAddress:
      "0x5555555555555555555555555555555555555555",
    recordId:
      "record-b",
    recordVersion:
      1,
    missionVersion:
      1,
    url:
      "https://b.example/records/b.json",
    recordHash:
      "d".repeat(64),
    subject:
      "mission-1",
    publishedAt:
      1_900_000_000,
    expiresAt:
      2_000_200_000,
  },
];

const pair: IndependentEvidencePair = {
  authorityA:
    "authority-a",
  authorityB:
    "authority-b",
  issuerA:
    "0x4444444444444444444444444444444444444444",
  issuerB:
    "0x5555555555555555555555555555555555555555",
};

describe(
  "seal mission safety",
  () => {
    it(
      "accepts a fully funded principal-owned corroborated acyclic mission",
      () => {
        expect(
          validateSealMissionEligibility(
            mission(),
            WALLET,
            effects,
            evidence,
            pair,
            1_950_000_000,
          ),
        ).toEqual([]);
      },
    );

    it(
      "rejects underfunding and missing corroboration",
      () => {
        const sameIssuer =
          evidence.map(
            (item) => ({
              ...item,
              issuerAddress:
                "0x4444444444444444444444444444444444444444" as const,
            }),
          );

        const errors =
          validateSealMissionEligibility(
            mission({
              fundedValue:
                BigInt("100000000000000000"),
            }),
            WALLET,
            effects,
            sameIssuer,
            null,
            1_950_000_000,
          );

        const joined =
          errors.join(" ");

        expect(joined).toContain(
          "underfunded",
        );
        expect(joined).toContain(
          "distinct issuer identities",
        );
        expect(joined).toContain(
          "No independent authority pair",
        );
      },
    );

    it(
      "rejects cyclic effect dependencies",
      () => {
        const cyclic: EffectSnapshot[] = [
          {
            ...effects[0],
            dependencyId:
              "effect-b",
          },
          {
            ...effects[1],
            dependencyId:
              "effect-a",
          },
        ];

        expect(
          validateEffectGraph(
            cyclic,
          ).join(" "),
        ).toContain(
          "cycle",
        );
      },
    );

    it(
      "rejects a non-principal and expired preparation window",
      () => {
        const errors =
          validateSealMissionEligibility(
            mission(),
            "0x9999999999999999999999999999999999999999",
            effects,
            evidence,
            pair,
            2_100_000_000,
          );

        const joined =
          errors.join(" ");

        expect(joined).toContain(
          "Only the mission principal",
        );
        expect(joined).toContain(
          "preparation deadline has passed",
        );
      },
    );
  },
);
