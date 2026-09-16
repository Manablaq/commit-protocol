import {
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  ExecutionResult,
  TransactionStatus,
  type TransactionHash,
} from "genlayer-js/types";
import {
  claimTransactionStorageKey,
  observeExternalDelivery,
  persistClaimTransaction,
  readPersistedClaimTransaction,
  type ExternalDeliveryChild,
} from "@/lib/genlayer-delivery";

const PARENT = `0x${"1".repeat(64)}` as TransactionHash;
const CHILD = `0x${"2".repeat(64)}` as TransactionHash;
const COORDINATOR = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" as const;
const RECIPIENT = "0x1111111111111111111111111111111111111111" as const;
const OTHER_RECIPIENT = "0x3333333333333333333333333333333333333333" as const;
const MISSION_ID = "mission-1";
const AMOUNT = BigInt("500000000000000000");
const EXPECTED = {
  coordinator: COORDINATOR,
  missionId: MISSION_ID,
  recipient: RECIPIENT,
  amount: AMOUNT,
};

function parentTransaction(
  overrides: Record<string, unknown> = {},
) {
  return {
    statusName: TransactionStatus.FINALIZED,
    txExecutionResultName: ExecutionResult.FINISHED_WITH_RETURN,
    to_address: COORDINATOR,
    from_address: RECIPIENT,
    sender: RECIPIENT,
    origin_address: RECIPIENT,
    txDataDecoded: {
      callData: {
        "": "claim_mission",
        args: [MISSION_ID],
      },
    },
    messages: [
      {
        recipient: RECIPIENT,
        value: AMOUNT.toString(),
        data: "",
        onAcceptance: false,
      },
    ],
    ...overrides,
  } as never;
}

function childTransaction(
  child: Partial<ExternalDeliveryChild> = {},
) {
  return {
    statusName: child.statusName,
    txExecutionResultName: child.executionResultName,
    to_address: child.recipient ?? RECIPIENT,
    value: (child.amount ?? AMOUNT).toString(),
  } as never;
}

function client(
  childIds: string[],
  child: ReturnType<typeof childTransaction>,
  parent = parentTransaction(),
) {
  return {
    getTriggeredTransactionIds: async () => childIds,
    getTransaction: async ({ hash }: { hash: string }) =>
      hash === PARENT ? parent : child,
  } as never;
}

describe(
  "strict external delivery observation",
  () => {
    it(
      "requires a verified finalized parent and child before reporting delivery",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            childTransaction({
              statusName: TransactionStatus.FINALIZED,
              executionResultName: ExecutionResult.FINISHED_WITH_RETURN,
            }),
          ),
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("DELIVERED");
        expect(result.child?.transactionId).toBe(CHILD);
        expect(result.child?.successful).toBe(true);
        expect(result.outboundMessage?.amount).toBe(AMOUNT);
      },
    );

    it(
      "reports a finalized execution error without authorizing retry",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            childTransaction({
              statusName: TransactionStatus.FINALIZED,
              executionResultName: ExecutionResult.FINISHED_WITH_ERROR,
            }),
          ),
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("FINALIZED_ERROR");
        expect(result.child?.successful).toBe(false);
        expect(result.reason).toContain("not proof of terminal non-delivery");
      },
    );

    it(
      "keeps a non-final child pending",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            childTransaction({
              statusName: TransactionStatus.ACCEPTED,
              executionResultName: "NOT_VOTED",
            }),
          ),
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("PENDING");
        expect(result.reason).toContain("Do not infer failure");
      },
    );

    it(
      "rejects a child whose recipient or amount is not exact",
      async () => {
        const wrongRecipient = await observeExternalDelivery(
          client(
            [CHILD],
            childTransaction({
              statusName: TransactionStatus.FINALIZED,
              executionResultName: ExecutionResult.FINISHED_WITH_RETURN,
              recipient: OTHER_RECIPIENT,
            }),
          ),
          PARENT,
          EXPECTED,
        );
        const wrongAmount = await observeExternalDelivery(
          client(
            [CHILD],
            childTransaction({
              statusName: TransactionStatus.FINALIZED,
              executionResultName: ExecutionResult.FINISHED_WITH_RETURN,
              amount: BigInt("600000000000000000"),
            }),
          ),
          PARENT,
          EXPECTED,
        );

        expect(wrongRecipient.phase).toBe("UNVERIFIED");
        expect(wrongAmount.phase).toBe("UNVERIFIED");
      },
    );

    it(
      "rejects parent transactions with the wrong mission, caller, or target",
      async () => {
        const wrongMission = await observeExternalDelivery(
          client([], childTransaction(), parentTransaction({
            txDataDecoded: {
              callData: { "": "claim_mission", args: ["other-mission"] },
            },
          })),
          PARENT,
          EXPECTED,
        );
        const wrongCaller = await observeExternalDelivery(
          client([], childTransaction(), parentTransaction({
            sender: OTHER_RECIPIENT,
          })),
          PARENT,
          EXPECTED,
        );
        const wrongTarget = await observeExternalDelivery(
          client([], childTransaction(), parentTransaction({
            to_address: OTHER_RECIPIENT,
          })),
          PARENT,
          EXPECTED,
        );

        expect(wrongMission.phase).toBe("UNVERIFIED");
        expect(wrongCaller.phase).toBe("UNVERIFIED");
        expect(wrongTarget.phase).toBe("UNVERIFIED");
      },
    );

    it(
      "does not interpret missing or ambiguous child IDs as success",
      async () => {
        const missing = await observeExternalDelivery(
          client([], childTransaction()),
          PARENT,
          EXPECTED,
        );
        const ambiguous = await observeExternalDelivery(
          client([CHILD, PARENT], childTransaction()),
          PARENT,
          EXPECTED,
        );
        const malformed = await observeExternalDelivery(
          client(["not-a-transaction-hash"], childTransaction()),
          PARENT,
          EXPECTED,
        );

        expect(missing.phase).toBe("UNVERIFIED");
        expect(missing.outboundMessage?.recipient).toBe(RECIPIENT);
        expect(ambiguous.phase).toBe("UNVERIFIED");
        expect(malformed.phase).toBe("UNVERIFIED");
      },
    );

    it(
      "does not interpret an RPC read error as terminal failure",
      async () => {
        const result = await observeExternalDelivery(
          {
            getTransaction: async () => parentTransaction(),
            getTriggeredTransactionIds: async () => {
              throw new Error("RPC unavailable");
            },
          } as never,
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("UNVERIFIED");
        expect(result.reason).toContain("Delivery is not proven");
      },
    );

    it(
      "fails closed when a stored amount is tampered with",
      async () => {
        const result = await observeExternalDelivery(
          client([], childTransaction()),
          PARENT,
          { ...EXPECTED, amount: BigInt("600000000000000000") },
        );

        expect(result.phase).toBe("UNVERIFIED");
        expect(result.reason).toContain("locally quoted amount");
      },
    );

    it(
      "persists only valid claim transaction hashes for re-observation",
      () => {
        const missionId = "delivery-test-mission";
        persistClaimTransaction(
          missionId,
          RECIPIENT,
          PARENT,
          AMOUNT,
        );

        expect(
          window.localStorage.getItem(
            claimTransactionStorageKey(missionId, RECIPIENT),
          ),
        ).toContain(PARENT);
        expect(
          readPersistedClaimTransaction(missionId, RECIPIENT)?.transactionId,
        ).toBe(PARENT);
        expect(
          readPersistedClaimTransaction(missionId, RECIPIENT)?.amount,
        ).toBe(AMOUNT);
        expect(
          readPersistedClaimTransaction(
            "different-mission",
            RECIPIENT,
          ),
        ).toBeNull();
        expect(
          readPersistedClaimTransaction(
            missionId,
            OTHER_RECIPIENT,
          ),
        ).toBeNull();
        window.localStorage.setItem(
          claimTransactionStorageKey(missionId, RECIPIENT),
          "not-a-hash",
        );
        expect(readPersistedClaimTransaction(missionId, RECIPIENT)).toBeNull();
      },
    );

    it(
      "keeps the transaction flow usable when browser storage is blocked",
      () => {
        const setItem = vi
          .spyOn(window.localStorage, "setItem")
          .mockImplementation(() => {
            throw new Error("storage blocked");
          });

        expect(() => {
          persistClaimTransaction(
            "storage-blocked-mission",
            RECIPIENT,
            PARENT,
            AMOUNT,
          );
        }).not.toThrow();

        setItem.mockRestore();
      },
    );
  },
);
