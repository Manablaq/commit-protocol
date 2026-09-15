import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/commit.py"

def test_studio_next_timestamp_uses_supported_transaction_clock():
    source = CONTRACT.read_text()
    assert "gl.vm.get_timestamp" not in source
    assert "time.time(" not in source

    tree = ast.parse(source)
    datetime_import = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "datetime"
        ),
        None,
    )
    assert datetime_import is not None
    imported = {alias.name for alias in datetime_import.names}
    assert imported == {"datetime", "timezone"}

    contract = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CommitProtocol"
    )
    timestamp_method = next(
        node
        for node in contract.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "t"
    )
    assert len(timestamp_method.body) == 1
    assert isinstance(timestamp_method.body[0], ast.Return)
    expression = ast.unparse(timestamp_method.body[0].value)
    assert expression == "int(datetime.now(timezone.utc).timestamp())"
