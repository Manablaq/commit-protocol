import {
  expect,
  test,
  type Page,
} from "@playwright/test";

const MOCK_WALLET =
  "0x1111111111111111111111111111111111111111";

async function installMockGenLayerWallet(
  page: Page,
) {
  await page.addInitScript(
    ({ address }) => {
      const calls: string[] = [];
      let snapInstalled = false;

      const provider = {
        request: async ({
          method,
        }: {
          method: string;
          params?: unknown;
        }) => {
          calls.push(method);

          if (
            method === "eth_requestAccounts"
            || method === "eth_accounts"
          ) {
            return [address];
          }

          if (method === "eth_chainId") {
            return "0xf22d";
          }

          if (method === "eth_getBalance") {
            return "0xde0b6b3a7640000";
          }

          if (method === "wallet_getSnaps") {
            return snapInstalled
              ? {
                  "npm:genlayer-wallet-plugin": {
                    id: "npm:genlayer-wallet-plugin",
                    version: "test",
                  },
                }
              : {};
          }

          if (method === "wallet_requestSnaps") {
            snapInstalled = true;

            return {
              "npm:genlayer-wallet-plugin": {
                id: "npm:genlayer-wallet-plugin",
                version: "test",
              },
            };
          }

          if (
            method === "wallet_addEthereumChain"
            || method === "wallet_switchEthereumChain"
          ) {
            return null;
          }

          throw new Error(
            `Unexpected mock wallet RPC: ${method}`,
          );
        },
        on: () => undefined,
        removeListener: () => undefined,
      };

      Object.defineProperty(
        window,
        "ethereum",
        {
          configurable: true,
          value: provider,
        },
      );

      Object.defineProperty(
        window,
        "__commitWalletRpcCalls",
        {
          configurable: true,
          value: calls,
        },
      );
    },
    {
      address: MOCK_WALLET,
    },
  );
}

test("COMMIT browser wallet performs the pinned GenLayer Snap preflight", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "1 GEN available",
      { exact: true },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "CREATE / MISSION",
      { exact: true },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(calls).toContain(
    "eth_requestAccounts",
  );
  expect(calls).toContain(
    "eth_chainId",
  );
  expect(calls).toContain(
    "wallet_getSnaps",
  );
  expect(calls).toContain(
    "wallet_requestSnaps",
  );
  expect(calls).toContain(
    "eth_accounts",
  );
  expect(calls).toContain(
    "eth_getBalance",
  );

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(liveRpcRequests).toEqual([]);
});

test("COMMIT connected wallet exposes supplier and effect preparation without writing", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "AUTHORIZE / SUPPLIER",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "PREPARE / EFFECT",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(
    liveRpcRequests,
  ).toEqual([]);
});

test("COMMIT connected wallet exposes evidence attestation and registration controls without writing", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "ISSUER / ATTEST",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "PRINCIPAL / REGISTER",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(
    liveRpcRequests,
  ).toEqual([]);
});

test("COMMIT connected wallet exposes mission sealing controls without writing", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "SEAL / MISSION",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "Roots are derived by the deployed coordinator from finalized state. The browser does not reimplement the hashing algorithm.",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(
    liveRpcRequests,
  ).toEqual([]);
});

test("COMMIT connected wallet exposes evaluation repair and recovery controls without writing", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "RESOLVE / MISSION",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "Allocation truth boundary",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(
    liveRpcRequests,
  ).toEqual([]);
});

test("COMMIT connected wallet exposes beneficiary claim and withdrawal receipt controls without writing", async ({
  page,
}) => {
  const liveRpcRequests: string[] = [];

  page.on("request", (request) => {
    if (
      request.url().startsWith(
        "https://studio-next.genlayer.com/api",
      )
    ) {
      liveRpcRequests.push(
        request.url(),
      );
    }
  });

  await installMockGenLayerWallet(
    page,
  );

  await page.goto("/app");

  await page
    .getByRole(
      "button",
      {
        name: /connect wallet/i,
      },
    )
    .first()
    .click();

  await expect(
    page.getByText(
      "CLAIM / WITHDRAW",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByText(
      "Receipt cross-check",
      {
        exact: true,
      },
    ),
  ).toBeVisible();

  const calls =
    await page.evaluate(() => (
      (
        window as typeof window & {
          __commitWalletRpcCalls?: string[];
        }
      ).__commitWalletRpcCalls ?? []
    ));

  expect(
    calls.includes(
      "eth_sendTransaction",
    ),
  ).toBe(false);

  expect(
    calls.includes(
      "wallet_invokeSnap",
    ),
  ).toBe(false);

  expect(
    liveRpcRequests,
  ).toEqual([]);
});

test("COMMIT application exposes the real wallet entry point", async ({
  page,
}) => {
  await page.goto("/app");

  await expect(
    page.getByRole(
      "heading",
      {
        level: 1,
        name: /CREATE\.\s*COMMIT\.\s*VERIFY\./i,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByRole(
      "button",
      { name: /connect wallet/i },
    ).first(),
  ).toBeVisible();

  await expect(
    page.getByText("Existing coordinator"),
  ).toBeVisible();
});

test("COMMIT verification center preserves provisional and finalized transaction truth", async ({
  page,
}) => {
  await page.route("**/api/v1/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema: "health",
        ok: true,
      }),
    });
  });

  await page.route("**/api/v1/transactions/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        found: true,
        genlayer_tx_id: "0xe2e",
        source_record_key: "tx-record",
        source_payload_digest: "digest",
        network_identity_basis: "certified",
        status_name: "ACCEPTED",
        execution_result: "FINISHED",
        successful: true,
        finalized: false,
        final_success: false,
        application_decision: "APPROVE",
      }),
    });
  });

  await page.goto("/verify");

  await expect(
    page.getByRole(
      "heading",
      {
        level: 1,
        name: "Verify what the protocol decided.",
      },
    ),
  ).toBeVisible();

  await page
    .getByLabel("GenLayer transaction ID")
    .fill("0xe2e");

  await page
    .getByRole(
      "button",
      { name: "Read transaction" },
    )
    .click();

  await expect(
    page.getByText("Accepted / provisional"),
  ).toBeVisible();

  await expect(
    page.getByText("Finalized", { exact: true }),
  ).toBeVisible();
});
