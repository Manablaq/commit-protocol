from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ARCHITECTURE_PACKET_SHA256 = (
    "9e3b70918e1bbba28f480606a204e94d46b7651b2e933ca39d712fae4e874585"
)

BUILD_CERTIFICATION_PACKET_SHA256 = (
    "4f49ac605fc79bc82404f0c37684172825fd6925734f72550d761015f48adde6"
)


def _path(
    relative: str,
) -> Path:
    return ROOT / relative


def _require_file(
    relative: str,
) -> Path:
    path = _path(
        relative
    )

    assert path.is_file(), (
        "required product UI file is missing: "
        + relative
    )

    return path


def _read(
    relative: str,
) -> str:
    return _require_file(
        relative
    ).read_text(
        encoding="utf-8"
    )


def _lower(
    relative: str,
) -> str:
    return _read(
        relative
    ).lower()


def _assert_contains_all(
    text: str,
    tokens: tuple[str, ...],
) -> None:
    missing = [
        token
        for token in tokens
        if token not in text
    ]

    assert not missing, (
        "required product UI tokens missing: "
        + repr(
            missing
        )
    )


def test_landing_experience_is_protocol_specific_and_wired() -> None:
    component = _lower(
        "components/landing/landing-experience.tsx"
    )

    page = _read(
        "app/page.tsx"
    )

    _assert_contains_all(
        component,
        (
            "commit",
            "semantic atomicity",
            "protocol truth",
            "/app",
        ),
    )

    assert "LandingExperience" in page


def test_original_commit_brand_and_reference_inspired_landing_exist() -> None:
    brand = _lower(
        "components/brand/commit-mark.tsx"
    )
    landing = _lower(
        "components/landing/landing-experience.tsx"
    )
    css = _lower(
        "app/globals.css"
    )

    _assert_contains_all(
        brand,
        (
            "commit-mark-primary",
            "commit-mark-hot",
            "commit-mark-cool",
            "commit-mark-seam",
            "viewbox",
        ),
    )

    _assert_contains_all(
        landing,
        (
            "make the",
            "prove the",
            "semantic atomicity",
            "protocol truth",
            "verification center",
            "/app",
        ),
    )

    _assert_contains_all(
        css,
        (
            ".commit-landing",
            ".commit-display",
            ".commit-angle",
            ".commit-poster",
            "clip-path",
            "--commit-hot",
            "--commit-cool",
        ),
    )

    assert "magnific" not in landing
    assert "sport" not in landing


def test_next16_build_configuration_is_explicit_and_stable() -> None:
    import json

    tsconfig = json.loads(
        _read(
            "tsconfig.json"
        )
    )
    next_config = _read(
        "next.config.ts"
    )
    gitignore = _read(
        ".gitignore"
    )

    assert tsconfig["compilerOptions"]["jsx"] == "react-jsx"
    assert ".next/dev/types/**/*.ts" in tsconfig["include"]
    assert "turbopack" in next_config
    assert "root: process.cwd()" in next_config
    assert ".next/" in gitignore.splitlines()


def test_application_shell_is_real_product_surface() -> None:
    component = _read(
        "components/application/application-shell.tsx"
    )
    flow = _read(
        "components/application/create-mission-flow.tsx"
    )
    client = _read(
        "lib/genlayer-browser.ts"
    )
    wallet_connection = _read(
        "lib/commit-wallet-connection.ts"
    )
    page = _read(
        "app/app/page.tsx"
    )

    _assert_contains_all(
        component,
        (
            "connectCommitWallet",
            "preflightCommitWallet",
            "CreateMissionFlow",
            "FundMissionFlow",
            "Connect wallet",
            "Existing coordinator",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "quoteCreateMission",
            "submitCreateMission",
            "trackCommitTransaction",
            "Sign &amp; create mission",
        ),
    )

    _assert_contains_all(
        client,
        (
            "studioDevnet",
            "create_mission",
            "get_mission",
            "fund_mission",
            "eth_getBalance",
            "validateFundingEligibility",
            "estimateTransactionFeesForWrite",
            "writeContract",
            "waitForFinalization",
            "FINISHED_WITH_RETURN",
            "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103",
        ),
    )

    assert "ApplicationShell" in page
    assert "createAccount" not in client
    assert "privateKey" not in client
    assert "eth_requestAccounts" in wallet_connection


def test_funding_flow_enforces_contract_preflight_before_signing() -> None:
    flow = _read(
        "components/application/fund-mission-flow.tsx"
    )
    client = _read(
        "lib/genlayer-browser.ts"
    )

    _assert_contains_all(
        flow,
        (
            "Preflight &amp; review funding",
            "Sign &amp; fund mission",
            "readMissionFundingSnapshot",
            "quoteFundMission",
            "submitFundMission",
            "trackCommitTransaction",
            "Verified funded value",
        ),
    )

    _assert_contains_all(
        client,
        (
            "Only the mission principal can fund this mission.",
            "Mission must still be PREPARING",
            "The mission preparation deadline has passed.",
            "Funding would exceed the mission budget.",
            "Wallet balance is insufficient",
        ),
    )

    app = _read(
        "components/application/application-shell.tsx"
    )

    assert "useEffect" not in flow
    assert 'useState(\n    initialMissionId,\n  );' in flow
    assert 'key={lastMissionId || "manual-funding"}' in app


def test_workspace_shell_is_wired_to_certified_read_client() -> None:
    component = _read(
        "components/workspace/workspace-shell.tsx"
    )

    page = _read(
        "app/verify/page.tsx"
    )

    _assert_contains_all(
        component,
        (
            "readHealth",
            "readProtocolIndex",
            "readTransaction",
        ),
    )

    lowered = component.lower()

    assert "fetch(" not in lowered
    assert "post" not in lowered
    assert "WorkspaceShell" in page


def test_workspace_prefills_exact_current_deployment_anchor() -> None:
    anchor = _read(
        "lib/deployment-anchor.ts"
    )
    workspace = _read(
        "components/workspace/workspace-shell.tsx"
    )

    _assert_contains_all(
        anchor,
        (
            "61997",
            "0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581",
            "0xc0e377d7a76893c253d61fcce42a320c6f5f41e5afad013a59dcbd279a998a50",
            "e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6",
            "FINALIZED",
            "FINISHED_WITH_RETURN",
        ),
    )

    assert "CURRENT_DEPLOYMENT_ANCHOR" in workspace
    assert workspace.count("useState<string>(") >= 4


def test_eslint_excludes_python_virtualenv_tooling() -> None:
    eslint_config = _read(
        "eslint.config.mjs"
    )

    assert '".venv/**"' in eslint_config


def test_index_overview_renders_exact_step7_index_fields() -> None:
    text = _lower(
        "components/workspace/index-overview.tsx"
    )

    _assert_contains_all(
        text,
        (
            "state_basis",
            "state_status",
            "network_identity_verified",
            "network_identity_basis",
            "protocol",
            "missions",
            "withdrawals",
        ),
    )


def test_transaction_inspector_renders_exact_step7_transaction_fields() -> None:
    text = _lower(
        "components/workspace/transaction-inspector.tsx"
    )

    _assert_contains_all(
        text,
        (
            "genlayer_tx_id",
            "status_name",
            "execution_result",
            "successful",
            "finalized",
            "final_success",
            "application_decision",
        ),
    )


def test_finality_card_keeps_provisional_finalized_and_durable_distinct() -> None:
    text = _lower(
        "components/workspace/finality-card.tsx"
    )

    _assert_contains_all(
        text,
        (
            "provisional",
            "finalized",
            "durable",
            "accepted",
        ),
    )

    assert "accepted = finalized" not in text
    assert "accepted === finalized" not in text


def test_provenance_card_exposes_storage_and_network_provenance() -> None:
    text = _lower(
        "components/workspace/provenance-card.tsx"
    )

    _assert_contains_all(
        text,
        (
            "source_record_key",
            "source_payload_digest",
            "network_identity_basis",
            "provenance",
        ),
    )


def test_semantic_graph_is_commit_specific_and_consequence_oriented() -> None:
    text = _lower(
        "components/workspace/semantic-graph.tsx"
    )

    _assert_contains_all(
        text,
        (
            "semantic",
            "mission",
            "evidence",
            "consequence",
            "finality",
        ),
    )


def test_state_boundary_has_truthful_loading_error_and_not_found_states() -> None:
    text = _lower(
        "components/workspace/state-boundary.tsx"
    )

    _assert_contains_all(
        text,
        (
            "loading",
            "error",
            "not found",
            "unavailable",
        ),
    )

    for forbidden in (
        "mock live",
        "fake live",
        "demo live",
    ):
        assert forbidden not in text


def test_visual_system_has_protocol_state_depth_responsiveness_and_reduced_motion() -> None:
    css = _lower(
        "app/globals.css"
    )

    _assert_contains_all(
        css,
        (
            "--provisional",
            "--finalized",
            "--evidence",
            "--signal",
            "radial-gradient",
            "linear-gradient",
            "@media (prefers-reduced-motion: reduce)",
            "@media (max-width: 960px)",
            "@media (max-width: 640px)",
        ),
    )


def test_product_surface_has_no_privileged_or_invented_state_authority() -> None:
    _require_file(
        "components/workspace/workspace-shell.tsx"
    )

    roots = (
        _path(
            "app"
        ),
        _path(
            "components"
        ),
        _path(
            "lib"
        ),
    )

    parts: list[str] = []

    for root in roots:
        assert root.exists(), (
            "required product UI source root is missing: "
            + str(
                root
            )
        )

        for path in sorted(
            root.rglob("*")
        ):
            if (
                path.is_file()
                and path.suffix.lower()
                in {
                    ".css",
                    ".js",
                    ".jsx",
                    ".mjs",
                    ".ts",
                    ".tsx",
                }
            ):
                parts.append(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

    combined = "\n".join(
        parts
    )

    forbidden = (
        "DATABASE_URL",
        "GENLAYER_RPC_URL",
        "COMMIT_READER_SENDER_ADDRESS",
        "run_backend_ingestion",
        "production_ingestion",
        "PostgresAtomicDriver",
        "DurableStateStore",
        "mock protocol state",
        "fake protocol state",
    )

    for token in forbidden:
        assert token not in combined


def test_component_integration_test_contract_exists() -> None:
    text = _read(
        "tests/frontend/product-ui.test.tsx"
    )

    _assert_contains_all(
        text,
        (
            "render",
            "screen",
            "finality",
            "provenance",
            "transaction",
        ),
    )


def test_browser_wallet_certification_matches_studio_dev_compatibility_flow() -> None:
    e2e = _read(
        "tests/e2e/product-ui.spec.ts"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )
    connector = _read(
        "lib/commit-wallet-connection.ts"
    )

    _assert_contains_all(
        e2e,
        (
            "wallet_getSnaps",
            "wallet_requestSnaps",
            "npm:genlayer-wallet-plugin",
            "eth_requestAccounts",
            "eth_accounts",
            "eth_getBalance",
            "eth_sendTransaction",
            "wallet_invokeSnap",
            "liveRpcRequests",
        ),
    )

    _assert_contains_all(
        connector,
        (
            "wallet_switchEthereumChain",
            "wallet_addEthereumChain",
            "4902",
            "tryEnableOptionalGenLayerSnap",
            "walletConnectionErrorMessage",
            "STUDIO_NETWORK_LABEL",
        ),
    )

    assert "Wallet / Studio Next 61997" in app
    assert "MetaMask + GenLayer Snap" not in app
    assert "GenLayer Snap support" not in app


def test_browser_e2e_contract_exists() -> None:
    text = _lower(
        "tests/e2e/product-ui.spec.ts"
    )

    _assert_contains_all(
        text,
        (
            "page",
            "/app",
            "/verify",
            "connect wallet",
            "transaction",
            "provisional",
            "finalized",
        ),
    )


def test_playwright_uses_isolated_base_url_and_current_routes() -> None:
    config = _read(
        "playwright.config.ts"
    )
    product = _read(
        "tests/e2e/product-ui.spec.ts"
    )
    responsive = _read(
        "tests/e2e/responsive-accessibility.spec.ts"
    )
    gitignore = _read(
        ".gitignore"
    )

    _assert_contains_all(
        config,
        (
            "PLAYWRIGHT_BASE_URL",
            "baseURL,",
        ),
    )

    _assert_contains_all(
        product,
        (
            "wallet_getSnaps",
            "wallet_requestSnaps",
            r"/CREATE\.\s*COMMIT\.\s*VERIFY\./i",
            'name: "Verify what the protocol decided."',
        ),
    )

    _assert_contains_all(
        responsive,
        (
            'page.goto(\n    "/verify",',
            "Launch the application",
            ".commit-nav-cta",
            ".commit-action",
            "Unsupported or empty CSS color",
        ),
    )

    assert '".ring-two"' not in responsive
    assert '".primary-action"' not in responsive
    assert "test-results/" in gitignore
    assert "playwright-report/" in gitignore


def test_supplier_and_effect_preparation_flow_is_contract_bound() -> None:
    client = _read(
        "lib/genlayer-browser.ts"
    )
    flow = _read(
        "components/application/prepare-mission-flow.tsx"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )

    _assert_contains_all(
        client,
        (
            "TransactionHashVariant.LATEST_FINAL",
            "is_supplier_authorized",
            "get_effect_by_index",
            "authorize_supplier",
            "prepare_effect",
            "prepare_effect_with_dependency",
            "Only the mission principal can authorize a supplier.",
            "Connected wallet is not an authorized supplier",
            "Prepared effects would exceed the mission budget.",
            "Effect expiry must be at or after the mission recovery deadline.",
            "Dependency effect does not exist on this mission.",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "AUTHORIZE / SUPPLIER",
            "PREPARE / EFFECT",
            "Preflight supplier",
            "Sign &amp; authorize supplier",
            "Preflight effect",
            "Sign &amp; prepare effect",
            "semantic allocation against the mission budget",
        ),
    )

    assert "PrepareMissionFlow" in app
    assert 'href="#prepare"' in app



def test_evidence_attestation_and_registration_are_provenance_bound() -> None:
    client = _read(
        "lib/genlayer-browser.ts"
    )
    flow = _read(
        "components/application/evidence-mission-flow.tsx"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )

    _assert_contains_all(
        client,
        (
            "get_authority",
            "get_evidence_attestation",
            "get_evidence",
            "get_evidence_by_index",
            "attest_evidence",
            "register_evidence",
            "TransactionHashVariant.LATEST_FINAL",
            "Connected wallet is not the registered authority issuer.",
            "Evidence URL is outside the registered authority origin/path.",
            "Evidence expiry must be at or after the mission recovery deadline.",
            "Only the mission principal can register evidence.",
            "Attestation mission version does not match the finalized mission version.",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "ISSUER / ATTEST",
            "PRINCIPAL / REGISTER",
            "Preflight attestation",
            "Sign &amp; attest evidence",
            "Preflight registration",
            "Sign &amp; register evidence",
            "immutable, versioned records",
        ),
    )

    assert "EvidenceMissionFlow" in app
    assert 'href="#evidence"' in app
    assert "register_authority" not in flow


def test_seal_flow_uses_contract_derived_roots_and_independent_evidence() -> None:
    client = _read(
        "lib/genlayer-seal.ts"
    )
    flow = _read(
        "components/application/seal-mission-flow.tsx"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )

    _assert_contains_all(
        client,
        (
            "TransactionHashVariant.LATEST_FINAL",
            "authorities_are_independent",
            "derive_effect_root",
            "derive_evidence_root",
            "seal_mission",
            "Only the mission principal can seal this mission.",
            "Mission needs at least two registered evidence records.",
            "Mission is underfunded for its prepared effects.",
            "Registered evidence must use at least two distinct issuer identities.",
            "Effect graph contains a cycle.",
            "Finalized mission roots do not match the reviewed seal roots.",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "SEAL / MISSION",
            "Preflight seal",
            "Sign &amp; seal mission",
            "contract-verified independent authority pair",
            "browser does not reimplement the hashing algorithm",
            "Finalized SEALED state verified with the exact reviewed roots.",
        ),
    )

    assert "Keccak" not in client
    assert "keccak" not in client.lower()
    assert "SealMissionFlow" in app
    assert 'href="#seal"' in app


def test_resolution_flow_separates_evaluation_repair_recovery_and_allocation() -> None:
    client = _read(
        "lib/genlayer-resolution.ts"
    )
    flow = _read(
        "components/application/resolution-mission-flow.tsx"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )

    _assert_contains_all(
        client,
        (
            "TransactionHashVariant.LATEST_FINAL",
            "get_evidence_failure",
            "get_evidence_repair",
            "get_mission_receipt",
            "evaluate_mission",
            "repair_evidence",
            "expire_mission",
            "Only the mission principal can repair evidence.",
            "Repair record version must be newer than the failed active record version.",
            "Recovery deadline has not passed.",
            "Finalized recovery did not produce the expected allocated ABORT state.",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "RESOLVE / MISSION",
            "Preflight evaluation",
            "Sign &amp; evaluate mission",
            "Preflight repair",
            "Sign &amp; repair evidence",
            "Preflight deadline recovery",
            "Sign &amp; expire mission",
            "wallet never calls apply_decision directly",
            "allocation_applied=true",
        ),
    )

    assert 'functionName:\n      "apply_decision"' not in client
    assert "ResolutionMissionFlow" in app
    assert 'href="#resolve"' in app


def test_claim_flow_uses_pull_payment_and_finalized_withdrawal_receipts() -> None:
    client = _read(
        "lib/genlayer-claim.ts"
    )
    flow = _read(
        "components/application/claim-mission-flow.tsx"
    )
    app = _read(
        "components/application/application-shell.tsx"
    )

    _assert_contains_all(
        client,
        (
            "TransactionHashVariant.LATEST_FINAL",
            "get_claimable",
            "get_mission_claimable",
            "get_withdrawal_count",
            "get_withdrawal",
            "get_withdrawal_by_index",
            "claim_mission",
            "Mission must be COMMITTED or ABORTED before claiming.",
            "Connected beneficiary has no claimable balance for this mission.",
            "Mission claimable balance was not zeroed after finalized claim.",
            "Expected exactly one matching DISPATCHED withdrawal",
            "Withdrawal direct-ID read does not match the by-index finalized record.",
        ),
    )

    _assert_contains_all(
        flow,
        (
            "CLAIM / WITHDRAW",
            "Preflight beneficiary claim",
            "Sign &amp; claim entitlement",
            "contract zeros the entitlement before",
            "Finalized withdrawal record verified",
            "external_withdrawal_recovery=false",
        ),
    )

    assert "externalWithdrawalRecovery" in client
    assert "value:" not in client.split(
        "export async function quoteClaimMission",
        1,
    )[1].split(
        "export async function submitClaimMission",
        1,
    )[0]
    assert "ClaimMissionFlow" in app
    assert 'href="#claim"' in app
