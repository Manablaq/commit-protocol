import {
  describe,
  expect,
  it,
} from "vitest";
import {
  appealChargeLabel,
  appealPhaseLabel,
  classifyAppealLifecycle,
  readAppealLifecycle,
} from "@/lib/genlayer-appeal";

const COORDINATOR = "0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581" as const;
const TX_ID = `0x${"1".repeat(64)}`;

function lifecycleClient({
  target = COORDINATOR,
  method = "evaluate_mission",
  missionId = "mission-001",
  executionResultName = "FINISHED_WITH_RETURN",
}: {
  target?: string;
  method?: string;
  missionId?: string;
  executionResultName?: string | null;
} = {}) {
  return {
    advanced: {
      getTransactionLifecycle: async () => ({
        storedStatus: "Finalized",
        projectedStatus: "Finalized",
        resolutionAction: "NoAction",
        resolutionSource: "Consensus",
        decisionId: "decision-001",
        decisionActive: true,
        evaluatedAt: 1_789_562_000,
      }),
    },
    getTransaction: async () => ({
      to_address: target,
      txDataDecoded: {
        type: "call",
        callData: new Map<string, unknown>([
          ["", method],
          ["args", [missionId]],
        ]),
      },
      txExecutionResultName: executionResultName,
    }),
  };
}

describe("GenLayer appeal lifecycle", () => {
  it("keeps processing, provisional, appealable, in-progress, and final states distinct", () => {
    expect(classifyAppealLifecycle({
      storedStatus: "Pending",
      decisionActive: false,
      canAppeal: false,
      executionSucceeded: null,
    })).toBe("UNDER_REVIEW");

    expect(classifyAppealLifecycle({
      storedStatus: "Accepted",
      decisionActive: true,
      canAppeal: false,
      executionSucceeded: null,
    })).toBe("PROVISIONAL");

    expect(classifyAppealLifecycle({
      storedStatus: "Accepted",
      decisionActive: true,
      canAppeal: true,
      executionSucceeded: null,
    })).toBe("APPEAL_OPEN");

    expect(classifyAppealLifecycle({
      storedStatus: "AppealRevealing",
      decisionActive: true,
      canAppeal: false,
      executionSucceeded: null,
    })).toBe("APPEAL_IN_PROGRESS");

    expect(classifyAppealLifecycle({
      storedStatus: "Finalized",
      decisionActive: true,
      canAppeal: false,
      executionSucceeded: true,
    })).toBe("FINALIZED");

    expect(classifyAppealLifecycle({
      storedStatus: "Finalized",
      decisionActive: true,
      canAppeal: false,
      executionSucceeded: false,
    })).toBe("FINALIZED_ERROR");

    expect(classifyAppealLifecycle({
      storedStatus: "Finalized",
      decisionActive: true,
      canAppeal: false,
      executionSucceeded: null,
    })).toBe("FINALIZED_UNKNOWN");
  });

  it("formats the authoritative appeal charge without inventing a quote", () => {
    expect(appealChargeLabel(null)).toBe("Not available");
    expect(appealChargeLabel(BigInt("1250000000000000000"))).toBe("1.25 GEN");
  });

  it("uses explicit lifecycle labels in the product language", () => {
    expect(appealPhaseLabel("PROVISIONAL")).toBe("Provisional verdict");
    expect(appealPhaseLabel("APPEAL_OPEN")).toBe("Appeal window open");
    expect(appealPhaseLabel("FINALIZED")).toBe("Final verdict");
  });

  it("binds a readable lifecycle to the certified coordinator and mission", async () => {
    const snapshot = await readAppealLifecycle(
      lifecycleClient() as never,
      TX_ID,
      {
        coordinator: COORDINATOR,
        missionId: "mission-001",
      },
    );

    expect(snapshot.transactionTarget).toBe(COORDINATOR);
    expect(snapshot.transactionFunctionName).toBe("evaluate_mission");
    expect(snapshot.transactionMissionId).toBe("mission-001");
    expect(snapshot.executionSucceeded).toBe(true);
    expect(snapshot.phase).toBe("FINALIZED");
  });

  it.each([
    ["wrong coordinator", { target: "0x0000000000000000000000000000000000000001" }, "different contract"],
    ["wrong method", { method: "create_mission" }, "not a coordinator evaluate_mission call"],
    ["wrong mission", { missionId: "mission-999" }, "different mission"],
  ])("rejects %s transaction identity", async (_label, transaction, message) => {
    await expect(
      readAppealLifecycle(
        lifecycleClient(transaction) as never,
        TX_ID,
        {
          coordinator: COORDINATOR,
          missionId: "mission-001",
        },
      ),
    ).rejects.toThrow(message);
  });

  it("never upgrades a finalized execution error into a durable verdict", async () => {
    const snapshot = await readAppealLifecycle(
      lifecycleClient({ executionResultName: "FINISHED_WITH_ERROR" }) as never,
      TX_ID,
    );

    expect(snapshot.executionSucceeded).toBe(false);
    expect(snapshot.phase).toBe("FINALIZED_ERROR");
  });
});
