"""Reference implementation for COMMIT's structural URL provenance rules."""

from __future__ import annotations

from collections.abc import Iterable

from .onchain import frame
from eth_hash.auto import keccak


class ProvenanceError(ValueError):
    pass


def _ascii(value: str, name: str, limit: int) -> str:
    if type(value) is not str or not value or len(value) > limit:
        raise ProvenanceError(f"invalid {name}")
    if any(ord(char) < 0x20 or ord(char) > 0x7E for char in value):
        raise ProvenanceError(f"invalid {name}")
    return value


def validate_authority(authority_id: str, host: str, path_prefix: str) -> None:
    _ascii(authority_id, "authority id", 64)
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in authority_id):
        raise ProvenanceError("invalid authority id")
    _ascii(host, "authority host", 253)
    if host != host.lower() or any(char in host for char in "/?:#@%\\"):
        raise ProvenanceError("invalid authority host")
    if host.startswith(".") or host.endswith(".") or ".." in host:
        raise ProvenanceError("invalid authority host")
    for label in host.split("."):
        if not 1 <= len(label) <= 63:
            raise ProvenanceError("invalid authority host")
        if label[0] == "-" or label[-1] == "-":
            raise ProvenanceError("invalid authority host")
        if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in label):
            raise ProvenanceError("invalid authority host")
    _ascii(path_prefix, "authority path prefix", 512)
    if not path_prefix.startswith("/") or "//" in path_prefix or any(
        marker in path_prefix for marker in ("?", "#", "%", "\\")
    ):
        raise ProvenanceError("invalid authority path prefix")
    if path_prefix != "/" and path_prefix.endswith("/"):
        raise ProvenanceError("invalid authority path prefix")
    if any(segment in (".", "..") for segment in path_prefix.split("/")):
        raise ProvenanceError("invalid authority path prefix")


def url_matches_authority(url: str, host: str, path_prefix: str) -> bool:
    try:
        validate_authority("authority", host, path_prefix)
        _ascii(url, "evidence url", 2048)
    except ProvenanceError:
        return False
    if not url.startswith("https://" + host):
        return False
    remainder = url[len("https://" + host):]
    if not remainder.startswith("/"):
        return False
    if any(marker in remainder for marker in ("?", "#", "%", "\\")):
        return False
    if remainder == "/":
        return path_prefix == "/"
    segments = remainder.split("/")
    if any(segment in ("", ".", "..") for segment in segments[1:]):
        return False
    if path_prefix == "/":
        return True
    if remainder == path_prefix:
        return True
    boundary = path_prefix if path_prefix.endswith("/") else path_prefix + "/"
    return remainder.startswith(boundary)


def evidence_leaf(
    *,
    evidence_id: str,
    authority_id: str,
    authority_version: int,
    issuer_address: str,
    record_id: str,
    record_version: int,
    mission_id: str,
    mission_version: int,
    url: str,
    record_hash: str,
    subject: str,
    published_at: int,
    expires_at: int,
) -> str:
    fields = (
        evidence_id,
        authority_id,
        str(authority_version),
        issuer_address,
        record_id,
        str(record_version),
        mission_id,
        str(mission_version),
        url,
        record_hash,
        subject,
        str(published_at),
        str(expires_at),
    )
    payload = "commit-evidence-leaf-v2" + "".join(
        frame(value) for value in fields
    )
    return keccak(payload.encode("utf-8")).hex()


def evidence_root(evidence_records: Iterable[dict[str, object]]) -> str:
    leaves = [
        evidence_leaf(
            evidence_id=str(record["evidence_id"]),
            authority_id=str(record["authority_id"]),
            authority_version=int(record["authority_version"]),
            issuer_address=str(record["issuer_address"]),
            record_id=str(record["record_id"]),
            record_version=int(record["record_version"]),
            mission_id=str(record["mission_id"]),
            mission_version=int(record["mission_version"]),
            url=str(record["url"]),
            record_hash=str(record["record_hash"]),
            subject=str(record["subject"]),
            published_at=int(record["published_at"]),
            expires_at=int(record["expires_at"]),
        )
        for record in evidence_records
    ]
    payload = "commit-evidence-root-v2" + frame(str(len(leaves)))
    payload += "".join(frame(leaf) for leaf in leaves)
    return keccak(payload.encode("utf-8")).hex()


def active_evidence_root(
    evidence_records: Iterable[dict[str, object]],
    repairs: dict[str, dict[str, object]],
) -> str:
    active_records = []

    for record in evidence_records:
        active_record = dict(record)
        evidence_id = str(record["evidence_id"])
        repair = repairs.get(evidence_id)

        if (
            repair is not None
            and str(repair.get("status", ""))
            == "READY"
        ):
            active_record.update(
                {
                    "authority_id": str(
                        repair["authority_id"]
                    ),
                    "authority_version": int(
                        repair["authority_version"]
                    ),
                    "issuer_address": str(
                        repair["issuer_address"]
                    ),
                    "record_id": str(
                        repair["record_id"]
                    ),
                    "record_version": int(
                        repair["record_version"]
                    ),
                    "url": str(
                        repair["url"]
                    ),
                    "record_hash": str(
                        repair["record_hash"]
                    ),
                    "published_at": int(
                        repair["published_at"]
                    ),
                    "expires_at": int(
                        repair["expires_at"]
                    ),
                }
            )

        active_records.append(active_record)

    return evidence_root(active_records)
