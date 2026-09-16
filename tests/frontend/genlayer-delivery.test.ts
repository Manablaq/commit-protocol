import {
  describe,
  expect,
  it,
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
const RECIPIENT = "0x1111111111111111111111111111111111111111" as const;
const OTHER_RECIPIENT = "0x3333333333333333333333333333333333333333" as const;
const AMOUNT = BigInt("500000000000000000");
const EXPECTED = {
  recipient: RECIPIENT,
  amount: AMOUNT,
};

function transaction(
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
  child: ReturnType<typeof transaction>,
) {
  return {
    getTriggeredTransactionIds: async () => childIds,
    getTransaction: async () => child,
  } as never;
}

describe(
  "strict external delivery observation",
  () => {
    it(
      "requires finalized successful execution before reporting delivery",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            transaction({
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
      },
    );

    it(
      "reports a definitive finalized execution error without authorizing retry",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            transaction({
              statusName: TransactionStatus.FINALIZED,
              executionResultName: ExecutionResult.FINISHED_WITH_ERROR,
            }),
          ),
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("FAILED");
        expect(result.child?.successful).toBe(false);
        expect(result.reason).toContain("does not automatically retry");
      },
    );

    it(
      "keeps a non-final child pending",
      async () => {
        const result = await observeExternalDelivery(
          client(
            [CHILD],
            transaction({
              statusName: TransactionStatus.ACCEPTED,
              executionResultName: ExecutionResult.NOT_VOTED,
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
      "rejects a successful child whose recipient or amount is not exact",
      async () => {
        const wrongRecipient = await observeExternalDelivery(
          client(
            [CHILD],
            transaction({
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
            transaction({
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
      "does not interpret missing or ambiguous child IDs as success",
      async () => {
        const missing = await observeExternalDelivery(
          client([], transaction()),
          PARENT,
          EXPECTED,
        );
        const ambiguous = await observeExternalDelivery(
          client([CHILD, PARENT], transaction()),
          PARENT,
          EXPECTED,
        );
        const malformed = await observeExternalDelivery(
          client(["not-a-transaction-hash"], transaction()),
          PARENT,
          EXPECTED,
        );

        expect(missing.phase).toBe("UNVERIFIED");
        expect(ambiguous.phase).toBe("UNVERIFIED");
        expect(malformed.phase).toBe("UNVERIFIED");
      },
    );

    it(
      "does not interpret an RPC read error as terminal failure",
      async () => {
        const result = await observeExternalDelivery(
          {
            getTriggeredTransactionIds: async () => {
              throw new Error("RPC unavailable");
            },
            getTransaction: async () => transaction(),
          } as never,
          PARENT,
          EXPECTED,
        );

        expect(result.phase).toBe("UNVERIFIED");
        expect(result.reason).toContain("No delivery outcome is claimed");
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
        window.localStorage.setItem(
          claimTransactionStorageKey(missionId, RECIPIENT),
          "not-a-hash",
        );
        expect(readPersistedClaimTransaction(missionId, RECIPIENT)).toBeNull();
      },
    );
  },
);
