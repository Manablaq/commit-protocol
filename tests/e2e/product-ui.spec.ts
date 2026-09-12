import {
  expect,
  test,
} from "@playwright/test";

test("COMMIT workspace preserves provisional and finalized transaction truth", async ({
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

  await page.goto("/app");

  await expect(
    page.getByText("Inspect semantic truth without becoming its authority."),
  ).toBeVisible();

  await page.getByLabel("GenLayer transaction ID").fill("0xe2e");
  await page.getByRole("button", { name: "Read transaction" }).click();

  await expect(
    page.getByText("Accepted / provisional"),
  ).toBeVisible();

  await expect(
    page.getByText("Finalized", { exact: true }),
  ).toBeVisible();
});
