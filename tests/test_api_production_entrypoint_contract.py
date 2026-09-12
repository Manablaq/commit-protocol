from __future__ import annotations

import ast
from pathlib import Path
import unittest


ENTRYPOINT = Path(
    "api/index.py"
)


class ProductionEntrypointContractTests(
    unittest.TestCase
):
    @staticmethod
    def _source() -> str:
        return ENTRYPOINT.read_text()

    def test_entrypoint_source_shape_and_app_export_are_exact(
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

        first = tree.body[
            0
        ]

        second = tree.body[
            1
        ]

        third = tree.body[
            2
        ]

        fourth = tree.body[
            3
        ]

        self.assertIsInstance(
            first,
            ast.Import,
        )

        self.assertEqual(
            [
                alias.name
                for alias in first.names
            ],
            [
                "os",
            ],
        )

        self.assertIsInstance(
            second,
            ast.Import,
        )

        self.assertEqual(
            [
                alias.name
                for alias in second.names
            ],
            [
                "psycopg",
            ],
        )

        self.assertIsInstance(
            third,
            ast.ImportFrom,
        )

        self.assertEqual(
            third.module,
            "backend.production_app",
        )

        self.assertEqual(
            [
                alias.name
                for alias in third.names
            ],
            [
                "build_production_app",
            ],
        )

        self.assertIsInstance(
            fourth,
            ast.Assign,
        )

        self.assertEqual(
            len(
                fourth.targets
            ),
            1,
        )

        self.assertIsInstance(
            fourth.targets[
                0
            ],
            ast.Name,
        )

        self.assertEqual(
            fourth.targets[
                0
            ].id,
            "app",
        )

        self.assertIsInstance(
            fourth.value,
            ast.Call,
        )

        self.assertIsInstance(
            fourth.value.func,
            ast.Name,
        )

        self.assertEqual(
            fourth.value.func.id,
            "build_production_app",
        )

    def test_entrypoint_injects_environment_and_connect_callable_without_calling_connect(
        self,
    ):
        source = self._source()

        tree = ast.parse(
            source
        )

        assignment = tree.body[
            3
        ]

        self.assertIsInstance(
            assignment,
            ast.Assign,
        )

        call = assignment.value

        self.assertIsInstance(
            call,
            ast.Call,
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

        environ = keywords[
            "environ"
        ]

        self.assertIsInstance(
            environ,
            ast.Attribute,
        )

        self.assertIsInstance(
            environ.value,
            ast.Name,
        )

        self.assertEqual(
            environ.value.id,
            "os",
        )

        self.assertEqual(
            environ.attr,
            "environ",
        )

        connect = keywords[
            "connect"
        ]

        self.assertIsInstance(
            connect,
            ast.Attribute,
        )

        self.assertIsInstance(
            connect.value,
            ast.Name,
        )

        self.assertEqual(
            connect.value.id,
            "psycopg",
        )

        self.assertEqual(
            connect.attr,
            "connect",
        )

        direct_connect_calls = []

        for node in ast.walk(
            tree
        ):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            function = node.func

            if (
                isinstance(
                    function,
                    ast.Attribute,
                )
                and isinstance(
                    function.value,
                    ast.Name,
                )
                and function.value.id
                == "psycopg"
                and function.attr
                == "connect"
            ):
                direct_connect_calls.append(
                    node
                )

        self.assertEqual(
            direct_connect_calls,
            [],
        )

    def test_entrypoint_contains_no_schema_live_rpc_filesystem_or_frontend_logic(
        self,
    ):
        source = self._source()

        forbidden = (
            "SCHEMA_SQL",
            "CREATE TABLE",
            "backend.network_adapter",
            "gen_call",
            "requests",
            "httpx",
            "sqlite",
            "open(",
            "Path(",
            "frontend",
            "nextjs",
            "react",
        )

        for term in forbidden:
            self.assertNotIn(
                term,
                source,
            )

    def test_entrypoint_contains_no_database_url_or_namespace_default_secret(
        self,
    ):
        source = self._source()

        forbidden = (
            "postgresql://",
            "postgres://",
            "commit-production-state",
            "localhost",
            "127.0.0.1",
            "password",
            "secret",
        )

        lowered = source.lower()

        for term in forbidden:
            self.assertNotIn(
                term.lower(),
                lowered,
            )


if __name__ == "__main__":
    unittest.main()
