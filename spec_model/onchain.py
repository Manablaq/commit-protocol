"""Pure-Python reference for COMMIT's current on-chain commitments.

The contract uses GenLayer's native ``Keccak256`` helper.  Client and test
code uses ``eth_hash`` so the byte construction can be compared without
reimplementing the contract runtime.  Text is restricted to printable ASCII
by the contract before these functions are called; addresses are compared in
the exact ``Address.as_hex`` spelling returned by GenLayer.
"""

from __future__ import annotations

from collections.abc import Iterable

from eth_hash.auto import keccak


def frame(value: str) -> str:
    if type(value) is not str:
        raise TypeError("framed values must be strings")
    return str(len(value)) + ":" + value


def _digest(payload: str) -> str:
    return keccak(payload.encode("utf-8")).hex()


def intent_digest(
    *,
    mission_id: str,
    objective: str,
    policy_digest: str,
    budget: int,
    refund_beneficiary: str,
    prepare_deadline: int,
    recovery_deadline: int,
) -> str:
    fields = (
        "1",
        mission_id,
        objective,
        policy_digest,
        str(budget),
        refund_beneficiary,
        str(prepare_deadline),
        str(recovery_deadline),
    )
    return _digest("commit-intent-v1" + "".join(frame(field) for field in fields))


def effect_leaf(
    *,
    effect_id: str,
    effect_digest: str,
    supplier: str,
    beneficiary: str,
    value: int,
    expiry: int,
) -> str:
    fields = (
        effect_id,
        effect_digest,
        supplier,
        beneficiary,
        str(value),
        str(expiry),
    )
    return _digest("commit-effect-leaf-v1" + "".join(frame(field) for field in fields))


def effect_root(effects: Iterable[dict[str, object]]) -> str:
    leaves = [
        effect_leaf(
            effect_id=str(effect["effect_id"]),
            effect_digest=str(effect["digest"]),
            supplier=str(effect["supplier"]),
            beneficiary=str(effect["beneficiary"]),
            value=int(effect["value"]),
            expiry=int(effect["expiry"]),
        )
        for effect in effects
    ]
    payload = "commit-effect-root-v1" + frame(str(len(leaves)))
    payload += "".join(frame(leaf) for leaf in leaves)
    return _digest(payload)
