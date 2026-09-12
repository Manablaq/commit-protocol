import {
  expect,
  test,
} from "@playwright/test";

const INDEX_FIXTURE = {
  schema: "commit-backend-index-query-v1",
  found: true,
  chain_id: 61997,
  contract_address: "0x00000000000000000000000000000000000000ab",
  requested_state_basis: "finalized",
  source_record_key: "stage10i-index-record",
  source_payload_digest:
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  block_number: 42,
  state_status: "finalized",
  state_basis: "finalized",
  network_identity_verified: true,
  network_identity_basis: "stage10i-test-fixture",
  protocol: {},
  missions: {},
  withdrawals: [],
};

async function routeHealth(
  page: import("@playwright/test").Page,
) {
  await page.route(
    "**/api/v1/health",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          schema: "health",
          ok: true,
        }),
      });
    },
  );
}

test("index request binds exact identity and renders finality plus provenance", async ({
  page,
}) => {
  await routeHealth(page);

  let observedIndexUrl = "";

  await page.route(
    "**/api/v1/index?**",
    async (route) => {
      observedIndexUrl = route.request().url();

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(INDEX_FIXTURE),
      });
    },
  );

  await page.goto("/app");

  await page.getByLabel("Chain ID").fill("61997");

  await page
    .getByLabel("Contract address")
    .fill("0x00000000000000000000000000000000000000ab");

  await page
    .getByLabel("State basis")
    .fill("finalized");

  await page
    .getByRole("button", {
      name: "Read index",
    })
    .click();

  await expect
    .poll(() => observedIndexUrl)
    .not
    .toBe("");

  const parsed = new URL(
    observedIndexUrl
  );

  expect(
    parsed.pathname
  ).toBe(
    "/api/v1/index"
  );

  expect(
    parsed.searchParams.get(
      "chain_id"
    )
  ).toBe(
    "61997"
  );

  expect(
    parsed.searchParams.get(
      "contract_address"
    )
  ).toBe(
    "0x00000000000000000000000000000000000000ab"
  );

  expect(
    parsed.searchParams.get(
      "state_basis"
    )
  ).toBe(
    "finalized"
  );

  await expect(
    page.getByText(
      "Finalized / durable"
    )
  ).toBeVisible();

  await expect(
    page.getByText(
      "stage10i-index-record"
    )
  ).toBeVisible();

  await expect(
    page
      .locator(
        ".provenance-card"
      )
      .getByText(
        "stage10i-test-fixture",
        {
          exact: true,
        },
      )
  ).toBeVisible();
});

test("landing and workspace stay usable without horizontal overflow across responsive viewports", async ({
  page,
}) => {
  const viewports = [
    {
      width: 1440,
      height: 1000,
    },
    {
      width: 834,
      height: 1112,
    },
    {
      width: 390,
      height: 844,
    },
  ];

  for (
    const viewport
    of viewports
  ) {
    await page.setViewportSize(
      viewport
    );

    await page.goto("/");

    await expect(
      page.getByRole(
        "heading",
        {
          level: 1,
          name:
            /Consequences should follow exact protocol truth/i,
        },
      )
    ).toBeVisible();

    await expect(
      page.getByRole(
        "link",
        {
          name:
            "Open protocol workspace",
        },
      )
    ).toBeVisible();

    const landingFits =
      await page.evaluate(
        () => (
          document.documentElement.scrollWidth
          <= window.innerWidth + 1
        ),
      );

    expect(
      landingFits
    ).toBe(
      true
    );

    await routeHealth(
      page
    );

    await page.goto(
      "/app"
    );

    await expect(
      page.getByLabel(
        "Chain ID"
      )
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "GenLayer transaction ID"
      )
    ).toBeVisible();

    const workspaceFits =
      await page.evaluate(
        () => (
          document.documentElement.scrollWidth
          <= window.innerWidth + 1
        ),
      );

    expect(
      workspaceFits
    ).toBe(
      true
    );
  }
});

test("workspace exposes semantic landmarks labels and keyboard focus", async ({
  page,
}) => {
  await routeHealth(page);

  await page.goto("/app");

  await expect(
    page.locator("main")
  ).toHaveCount(1);

  await expect(
    page.getByRole(
      "heading",
      {
        level: 1,
      },
    )
  ).toHaveCount(1);

  await expect(
    page.getByLabel(
      "Chain ID"
    )
  ).toHaveAttribute(
    "required",
    ""
  );

  await expect(
    page.getByLabel(
      "Contract address"
    )
  ).toHaveAttribute(
    "required",
    ""
  );

  await expect(
    page.getByLabel(
      "State basis"
    )
  ).toHaveAttribute(
    "required",
    ""
  );

  await expect(
    page.getByLabel(
      "GenLayer transaction ID"
    )
  ).toHaveAttribute(
    "required",
    ""
  );

  await expect(
    page.getByRole(
      "button",
      {
        name: "Read index",
      },
    )
  ).toBeVisible();

  await expect(
    page.getByRole(
      "button",
      {
        name: "Read transaction",
      },
    )
  ).toBeVisible();

  await page.keyboard.press(
    "Tab"
  );

  const firstFocusedLabel =
    await page.evaluate(
      () => (
        document.activeElement
          ?.getAttribute(
            "aria-label"
          )
        ?? ""
      ),
    );

  expect(
    firstFocusedLabel
  ).toBe(
    "Back to COMMIT home"
  );
});

test("reduced motion and core foreground tokens meet deterministic accessibility gates", async ({
  page,
}) => {
  await page.emulateMedia({
    reducedMotion:
      "reduce",
  });

  await page.goto("/");

  const reducedMotion =
    await page.evaluate(
      () => (
        window.matchMedia(
          "(prefers-reduced-motion: reduce)"
        ).matches
      ),
    );

  expect(
    reducedMotion
  ).toBe(
    true
  );

  const motionDurations =
    await page.evaluate(
      () => {
        const ring =
          document.querySelector(
            ".ring-two"
          );

        const action =
          document.querySelector(
            ".primary-action"
          );

        if (
          ring === null
          || action === null
        ) {
          throw new Error(
            "motion targets missing"
          );
        }

        return {
          animationDuration:
            getComputedStyle(
              ring
            ).animationDuration,

          transitionDuration:
            getComputedStyle(
              action
            ).transitionDuration,
        };
      },
    );

  expect(
    parseFloat(
      motionDurations.animationDuration
    )
  ).toBeLessThanOrEqual(
    0.001
  );

  expect(
    parseFloat(
      motionDurations.transitionDuration
    )
  ).toBeLessThanOrEqual(
    0.001
  );

  const ratios =
    await page.evaluate(
      () => {
        const style =
          getComputedStyle(
            document.documentElement
          );

        function channel(
          value: number,
        ) {
          const normalized =
            value / 255;

          return normalized <= 0.03928
            ? normalized / 12.92
            : Math.pow(
                (
                  normalized
                  + 0.055
                )
                / 1.055,
                2.4,
              );
        }

        function luminance(
          hex: string,
        ) {
          const normalized =
            hex.trim().replace(
              "#",
              ""
            );

          const red =
            parseInt(
              normalized.slice(
                0,
                2,
              ),
              16,
            );

          const green =
            parseInt(
              normalized.slice(
                2,
                4,
              ),
              16,
            );

          const blue =
            parseInt(
              normalized.slice(
                4,
                6,
              ),
              16,
            );

          return (
            0.2126 * channel(red)
            + 0.7152 * channel(green)
            + 0.0722 * channel(blue)
          );
        }

        function contrast(
          foreground: string,
          background: string,
        ) {
          const first =
            luminance(
              foreground
            );

          const second =
            luminance(
              background
            );

          const light =
            Math.max(
              first,
              second
            );

          const dark =
            Math.min(
              first,
              second
            );

          return (
            (light + 0.05)
            / (dark + 0.05)
          );
        }

        const background =
          style.getPropertyValue(
            "--background"
          );

        const tokens = [
          "--text",
          "--muted",
          "--muted-strong",
          "--signal",
          "--evidence",
          "--provisional",
          "--finalized",
        ];

        return Object.fromEntries(
          tokens.map(
            (token) => [
              token,
              contrast(
                style.getPropertyValue(
                  token
                ),
                background,
              ),
            ],
          )
        );
      },
    );

  for (
    const ratio
    of Object.values(
      ratios
    )
  ) {
    expect(
      ratio
    ).toBeGreaterThanOrEqual(
      4.5
    );
  }
});
