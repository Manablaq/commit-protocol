from __future__ import annotations

import ast
from pathlib import Path
import unittest


SCRIPT = Path(
    "scripts/bootstrap_backend_schema.py"
)


class SchemaBootstrapScriptContractTests(
    unittest.TestCase
):
    @staticmethod
    def _source() -> str:
        return SCRIPT.read_text()

    def test_script_source_shape_has_explicit_main_guard(
        self,
    ):
        source = self._source()

        tree = ast.parse(
            source
        )

        self.assertEqual(
            len(
                tree.body
            ),
            4,
        )

        self.assertIsInstance(
            tree.body[
                0
            ],
            ast.Import,
        )

        self.assertEqual(
            [
                alias.name
                for alias in tree.body[
                    0
                ].names
            ],
            [
                "os",
            ],
        )

        self.assertIsInstance(
            tree.body[
                1
            ],
            ast.Import,
        )

        self.assertEqual(
            [
                alias.name
                for alias in tree.body[
                    1
                ].names
            ],
            [
                "psycopg",
            ],
        )

        self.assertIsInstance(
            tree.body[
                2
            ],
            ast.ImportFrom,
        )

        self.assertEqual(
            tree.body[
                2
            ].module,
            "backend.schema_bootstrap",
        )

        self.assertEqual(
            [
                alias.name
                for alias in tree.body[
                    2
                ].names
            ],
            [
                "bootstrap_schema",
            ],
        )

        guard = tree.body[
            3
        ]

        self.assertIsInstance(
            guard,
            ast.If,
        )

        self.assertEqual(
            ast.unparse(
                guard.test
            ),
            "__name__ == '__main__'",
        )

    def test_main_guard_injects_environment_and_connect_callable(
        self,
    ):
        source = self._source()

        tree = ast.parse(
            source
        )

        guard = tree.body[
            3
        ]

        self.assertIsInstance(
            guard,
            ast.If,
        )

        self.assertEqual(
            len(
                guard.body
            ),
            1,
        )

        expression = guard.body[
            0
        ]

        self.assertIsInstance(
            expression,
            ast.Expr,
        )

        call = expression.value

        self.assertIsInstance(
            call,
            ast.Call,
        )

        self.assertIsInstance(
            call.func,
            ast.Name,
        )

        self.assertEqual(
            call.func.id,
            "bootstrap_schema",
        )

        self.assertEqual(
            call.args,
            [],
        )

        keywords = {
            keyword.arg: keyword.value
            for keyword in call.keywords
        }

        self.assertEqual(
            set(
                keywords
            ),
            {
                "environ",
                "connect",
            },
        )

        self.assertEqual(
            ast.unparse(
                keywords[
                    "environ"
                ]
            ),
            "os.environ",
        )

        self.assertEqual(
            ast.unparse(
                keywords[
                    "connect"
                ]
            ),
            "psycopg.connect",
        )

    def test_script_does_not_duplicate_schema_or_contain_public_live_rpc_logic(
        self,
    ):
        source = self._source()

        forbidden = (
            "SCHEMA_SQL",
            "CREATE TABLE",
            "FastAPI",
            "backend.service_api",
            "backend.production_app",
            "backend.network_adapter",
            "gen_call",
            "requests",
            "httpx",
            "frontend",
            "react",
            "nextjs",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

    def test_script_contains_no_database_secret_or_default_url(
        self,
    ):
        source = self._source()

        lowered = source.lower()

        forbidden = (
            "postgresql://",
            "postgres://",
            "localhost",
            "127.0.0.1",
            "password",
            "secret",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                lowered,
            )


if __name__ == "__main__":
    unittest.main()
