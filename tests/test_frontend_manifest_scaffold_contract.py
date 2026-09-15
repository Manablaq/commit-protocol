from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

ARCHITECTURE_PACKET_SHA256 = (
    "9e3b70918e1bbba28f480606a204e94d46b7651b2e933ca39d712fae4e874585"
)

DEPENDENCY_PREFLIGHT_PACKET_SHA256 = (
    "a6c6b2aa521326b6b5f8e547874db6b4fe9e0a573d9daca527429a0a72bc4c11"
)


RUNTIME_DEPENDENCIES = {
    "genlayer-js": "github:genlayerlabs/genlayer-js#facd9e9dc9a289d0110fe3b5b1a14a2938fe6e01",
    "lucide-react": "1.45.0",
    "motion": "13.1.1",
    "next": "16.3.3",
    "react": "19.3.0",
    "react-dom": "19.3.0",
}


DEVELOPMENT_DEPENDENCIES = {
    "@playwright/test": "1.63.0",
    "@tailwindcss/postcss": "4.3.3",
    "@testing-library/dom": "10.4.1",
    "@testing-library/jest-dom": "7.0.1",
    "@testing-library/react": "16.3.3",
    "@types/node": "24.13.4",
    "@types/react": "19.3.0",
    "@types/react-dom": "19.3.0",
    "eslint": "9.39.5",
    "eslint-config-next": "16.3.3",
    "jsdom": "30.0.1",
    "postcss": "8.5.28",
    "tailwindcss": "4.3.3",
    "typescript": "6.0.3",
    "vitest": "5.0.0",
}


REQUIRED_SCRIPTS = {
    "build": "next build",
    "dev": "next dev",
    "lint": "eslint .",
    "start": "next start",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
}


CORE_SCAFFOLD_FILES = (
    "app/globals.css",
    "app/layout.tsx",
    "app/page.tsx",
    "app/app/page.tsx",
)


CONFIG_FILES = (
    "eslint.config.mjs",
    "next.config.ts",
    "playwright.config.ts",
    "postcss.config.mjs",
    "tsconfig.json",
    "vitest.config.ts",
    "vitest.setup.ts",
)


PUBLIC_READ_ROUTES = (
    "/api/v1/health",
    "/api/v1/index",
    "/api/v1/transactions/",
)


FORBIDDEN_BROWSER_TOKENS = (
    "DATABASE_URL",
    "GENLAYER_RPC_URL",
    "COMMIT_READER_SENDER_ADDRESS",
    "run_backend_ingestion",
    "production_ingestion",
    "PostgresAtomicDriver",
    "DurableStateStore",
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
        f"required frontend scaffold file is missing: {relative}"
    )

    return path


def _read_json(
    relative: str,
) -> dict:
    path = _require_file(
        relative
    )

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert isinstance(
        value,
        dict,
    )

    return value


def _frontend_text() -> str:
    roots = [
        _path("app"),
        _path("components"),
        _path("lib"),
    ]

    files = []

    for root in roots:
        if not root.exists():
            continue

        files.extend(
            path
            for path in root.rglob("*")
            if (
                path.is_file()
                and path.suffix
                in {
                    ".css",
                    ".js",
                    ".jsx",
                    ".mjs",
                    ".ts",
                    ".tsx",
                }
            )
        )

    assert files, (
        "frontend browser/source surface is missing"
    )

    return "\n".join(
        path.read_text(
            encoding="utf-8"
        )
        for path in files
    )


def test_package_manifest_metadata_is_frozen() -> None:
    package = _read_json(
        "package.json"
    )

    assert package.get(
        "private"
    ) is True

    assert package.get(
        "packageManager"
    ) == "npm@11.19.0"

    assert package.get(
        "engines"
    ) == {
        "node": "24.20.0",
        "npm": "11.19.0",
    }


def test_runtime_dependencies_are_exact() -> None:
    package = _read_json(
        "package.json"
    )

    assert package.get(
        "dependencies"
    ) == RUNTIME_DEPENDENCIES


def test_development_dependencies_are_exact() -> None:
    package = _read_json(
        "package.json"
    )

    assert package.get(
        "devDependencies"
    ) == DEVELOPMENT_DEPENDENCIES


def test_frontend_scripts_are_exact() -> None:
    package = _read_json(
        "package.json"
    )

    assert package.get(
        "scripts"
    ) == REQUIRED_SCRIPTS


def test_npm_lockfile_is_exactly_rooted_to_manifest() -> None:
    package = _read_json(
        "package.json"
    )

    lock = _read_json(
        "package-lock.json"
    )

    assert lock.get(
        "lockfileVersion"
    ) == 3

    root = (
        lock.get(
            "packages",
            {},
        ).get(
            "",
            {},
        )
    )

    assert root.get(
        "dependencies"
    ) == package.get(
        "dependencies"
    )

    assert root.get(
        "devDependencies"
    ) == package.get(
        "devDependencies"
    )

    assert root.get(
        "engines"
    ) == package.get(
        "engines"
    )


def test_next_app_router_core_scaffold_exists() -> None:
    for relative in CORE_SCAFFOLD_FILES:
        _require_file(
            relative
        )


def test_frontend_configuration_scaffold_exists() -> None:
    for relative in CONFIG_FILES:
        _require_file(
            relative
        )


def test_typescript_configuration_is_strict() -> None:
    config = _read_json(
        "tsconfig.json"
    )

    compiler = config.get(
        "compilerOptions",
        {},
    )

    assert compiler.get(
        "strict"
    ) is True

    assert compiler.get(
        "noEmit"
    ) is True

    assert compiler.get(
        "jsx"
    ) == "react-jsx"


def test_tailwind_postcss_configuration_is_bound() -> None:
    text = _require_file(
        "postcss.config.mjs"
    ).read_text(
        encoding="utf-8"
    )

    assert "@tailwindcss/postcss" in text

    globals_text = _require_file(
        "app/globals.css"
    ).read_text(
        encoding="utf-8"
    )

    assert 'import "tailwindcss"' in (
        globals_text
        .replace(
            "@import",
            "import",
        )
    )


def test_step7_get_api_is_the_frontend_protocol_state_authority() -> None:
    text = _require_file(
        "lib/api.ts"
    ).read_text(
        encoding="utf-8"
    )

    for route in PUBLIC_READ_ROUTES:
        assert route in text

    lowered = text.lower()

    assert "post(" not in lowered
    assert 'method: "post"' not in lowered
    assert "method: 'post'" not in lowered


def test_browser_surface_has_no_server_or_ingestion_authority() -> None:
    for relative in (
        "app/page.tsx",
        "app/app/page.tsx",
        "lib/api.ts",
    ):
        _require_file(
            relative
        )

    text = _frontend_text()

    for token in FORBIDDEN_BROWSER_TOKENS:
        assert token not in text


def test_finality_truth_and_provenance_scaffold_is_explicit() -> None:
    state_text = _require_file(
        "lib/protocol-state.ts"
    ).read_text(
        encoding="utf-8"
    ).lower()

    provenance_text = _require_file(
        "lib/provenance.ts"
    ).read_text(
        encoding="utf-8"
    ).lower()

    assert "provisional" in state_text
    assert "finalized" in state_text
    assert "durable" in state_text

    assert "source" in provenance_text
    assert "observed" in provenance_text

    combined = (
        state_text
        + "\n"
        + provenance_text
    )

    assert "mock protocol state" not in combined
    assert "fake protocol state" not in combined
