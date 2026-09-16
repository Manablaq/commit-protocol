import {
  describe,
  expect,
  it,
} from "vitest";
import {
  appealChargeLabel,
  appealPhaseLabel,
  classifyAppealLifecycle,
} from "@/lib/genlayer-appeal";

describe("GenLayer appeal lifecycle", () => {
  it("keeps processing, provisional, appealable, in-progress, and final states distinct", () => {
    expect(classifyAppealLifecycle({
      storedStatus: "Pending",
      decisionActive: false,
      canAppeal: false,
    })).toBe("UNDER_REVIEW");

    expect(classifyAppealLifecycle({
      storedStatus: "Accepted",
      decisionActive: true,
      canAppeal: false,
    })).toBe("PROVISIONAL");

    expect(classifyAppealLifecycle({
      storedStatus: "Accepted",
      decisionActive: true,
      canAppeal: true,
    })).toBe("APPEAL_OPEN");

    expect(classifyAppealLifecycle({
      storedStatus: "AppealRevealing",
      decisionActive: true,
      canAppeal: false,
    })).toBe("APPEAL_IN_PROGRESS");

    expect(classifyAppealLifecycle({
      storedStatus: "Finalized",
      decisionActive: true,
      canAppeal: false,
    })).toBe("FINALIZED");
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
});
