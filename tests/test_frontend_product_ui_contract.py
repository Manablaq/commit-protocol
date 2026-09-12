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


def test_workspace_shell_is_wired_to_certified_read_client() -> None:
    component = _read(
        "components/workspace/workspace-shell.tsx"
    )

    page = _read(
        "app/app/page.tsx"
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


def test_browser_e2e_contract_exists() -> None:
    text = _lower(
        "tests/e2e/product-ui.spec.ts"
    )

    _assert_contains_all(
        text,
        (
            "page",
            "/app",
            "transaction",
            "provisional",
            "finalized",
        ),
    )
