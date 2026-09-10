"""Canonical COMMIT object encoding used by tests and future clients.

This module intentionally accepts a small JSON-compatible domain. Contract
storage objects must first be converted to one of the explicit protocol
schemas; arbitrary Python objects are rejected.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


PROTOCOL = "commit-semantic-atomicity"
REVISION = 1
_HEX_32 = re.compile(r"^[0-9a-f]{64}$")
_ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")


class CanonicalError(ValueError):
    pass


def _validate(value: Any, path: str = "$") -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if type(value) is int:
        if value < 0 or value >= 2**256:
            raise CanonicalError(f"{path}: integer outside u256")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate(item, f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or not key:
                raise CanonicalError(f"{path}: keys must be nonempty strings")
            _validate(item, f"{path}.{key}")
        return
    raise CanonicalError(f"{path}: unsupported {type(value).__name__}")


def encode(object_type: str, body: dict[str, Any]) -> bytes:
    if not object_type or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", object_type):
        raise CanonicalError("invalid object type")
    if type(body) is not dict:
        raise CanonicalError("body must be an object")
    envelope = {
        "body": body,
        "object_type": object_type,
        "protocol": PROTOCOL,
        "revision": REVISION,
    }
    _validate(envelope)
    return json.dumps(
        envelope, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(object_type: str, body: dict[str, Any]) -> str:
    return hashlib.sha256(encode(object_type, body)).hexdigest()


def require_hash(value: str, name: str) -> str:
    if not _HEX_32.fullmatch(value):
        raise CanonicalError(f"{name} must be lowercase SHA-256 hex")
    return value


def require_address(value: str, name: str) -> str:
    if not _ADDRESS.fullmatch(value):
        raise CanonicalError(f"{name} must be lowercase 20-byte address")
    return value


def effect_body(*, domain_hash: str, mission_id: str, version: int,
                effect_id: str, recipient: str, amount_wei: int,
                payload_hash: str, nonce: int, expires_at: int) -> dict[str, Any]:
    if not mission_id or len(mission_id.encode()) > 96:
        raise CanonicalError("invalid mission_id")
    if not effect_id or len(effect_id.encode()) > 64:
        raise CanonicalError("invalid effect_id")
    return {
        "amount_wei": amount_wei,
        "domain_hash": require_hash(domain_hash, "domain_hash"),
        "effect_id": effect_id,
        "expires_at": expires_at,
        "mission_id": mission_id,
        "nonce": nonce,
        "payload_hash": require_hash(payload_hash, "payload_hash"),
        "recipient": require_address(recipient, "recipient"),
        "version": version,
    }
