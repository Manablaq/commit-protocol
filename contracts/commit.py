# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""COMMIT semantic-atomicity coordinator with native-GEN escrow.

The contract binds a mission's intent, evidence, and effect graph; evaluates
sealed evidence through independent GenLayer reads; applies the result only
through a finalized self-message; and allocates escrow into claimable
entitlements in one state transition. External withdrawals remain one-way
until the network provides an authenticated delivery/non-delivery proof.
"""

from datetime import datetime, timezone
import json

import genlayer as gl

Address = gl.Address
Keccak256 = gl.Keccak256
TreeMap = gl.storage.TreeMap
u256 = gl.u256
_get_contract_at = gl.contract.get_at

PROTOCOL = "commit"
REVISION = "0.7.0-reviewable-manifest"
STATE_PREPARING = "PREPARING"
STATE_SEALED = "SEALED"
STATE_DECISION_PENDING = "DECISION_PENDING"
STATE_COMMITTED = "COMMITTED"
STATE_ABORTED = "ABORTED"
WITHDRAWAL_DISPATCHED = "DISPATCHED"
MAX_TEXT = 512
MAX_EFFECTS = 32
MAX_EVIDENCE = 16
MAX_REASON = 128
MAX_REMOTE_BODY = 16 * 1024
MAX_U256 = (1 << 256) - 1
EVIDENCE_SCHEMA = "commit-evidence-v2"
POLICY_RULE = "all-evidence-and-effects-v1"
POLICY_DIGEST = "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103"
DECISION_ENVELOPE = "commit-decision-v2"
RECEIPT_SCHEMA = "commit-mission-receipt-v1"
MANIFEST_SCHEMA = "commit-mission-manifest-v1"


@gl.evm.contract_interface
class _NativeRecipient:
    class View:
        pass

    class Write:
        pass


class CommitProtocol(gl.contract.Contract):
    owner: gl.Address
    mission_count: gl.u256
    mission_exists: TreeMap[str, bool]
    mission_key: TreeMap[str, str]
    mission_principal: TreeMap[str, Address]
    mission_state: TreeMap[str, str]
    mission_objective: TreeMap[str, str]
    mission_policy_digest: TreeMap[str, str]
    mission_intent_digest: TreeMap[str, str]
    mission_effect_root: TreeMap[str, str]
    mission_evidence_root: TreeMap[str, str]
    mission_budget: TreeMap[str, u256]
    mission_funded_value: TreeMap[str, u256]
    mission_prepared_value: TreeMap[str, u256]
    mission_refund_beneficiary: TreeMap[str, Address]
    mission_refund_entitlement: TreeMap[str, u256]
    mission_decision_nonce: TreeMap[str, str]
    mission_allocation_applied: TreeMap[str, bool]
    mission_evidence_count: TreeMap[str, u256]
    mission_decision: TreeMap[str, str]
    mission_reason_code: TreeMap[str, str]
    mission_evaluation_count: TreeMap[str, u256]
    mission_prepare_deadline: TreeMap[str, u256]
    mission_recovery_deadline: TreeMap[str, u256]
    mission_created_at: TreeMap[str, u256]
    mission_version: TreeMap[str, u256]
    mission_effect_count: TreeMap[str, u256]
    effect_exists: TreeMap[str, bool]
    effect_mission: TreeMap[str, str]
    effect_supplier: TreeMap[str, Address]
    effect_id: TreeMap[str, str]
    effect_digest: TreeMap[str, str]
    effect_parent: TreeMap[str, str]
    effect_beneficiary: TreeMap[str, Address]
    effect_value: TreeMap[str, u256]
    effect_expiry: TreeMap[str, u256]
    mission_effect_key: TreeMap[str, str]
    authority_exists: TreeMap[str, bool]
    authority_active: TreeMap[str, bool]
    authority_host: TreeMap[str, str]
    authority_path_prefix: TreeMap[str, str]
    authority_issuer: TreeMap[str, Address]
    authority_version: TreeMap[str, u256]
    supplier_authorized: TreeMap[str, bool]
    supplier_count: TreeMap[str, u256]
    evidence_exists: TreeMap[str, bool]
    evidence_mission: TreeMap[str, str]
    evidence_id: TreeMap[str, str]
    evidence_authority: TreeMap[str, str]
    evidence_url: TreeMap[str, str]
    evidence_record_hash: TreeMap[str, str]
    evidence_subject: TreeMap[str, str]
    evidence_expires_at: TreeMap[str, u256]
    evidence_authority_version: TreeMap[str, u256]
    evidence_issuer: TreeMap[str, Address]
    evidence_record_id: TreeMap[str, str]
    evidence_record_version: TreeMap[str, u256]
    evidence_mission_version: TreeMap[str, u256]
    evidence_published_at: TreeMap[str, u256]
    mission_evidence_key: TreeMap[str, str]

    attestation_exists: TreeMap[str, bool]
    attestation_authority: TreeMap[str, str]
    attestation_authority_version: TreeMap[str, u256]
    attestation_issuer: TreeMap[str, Address]
    attestation_record_id: TreeMap[str, str]
    attestation_record_version: TreeMap[str, u256]
    attestation_mission: TreeMap[str, str]
    attestation_mission_version: TreeMap[str, u256]
    attestation_url: TreeMap[str, str]
    attestation_record_hash: TreeMap[str, str]
    attestation_published_at: TreeMap[str, u256]
    attestation_expires_at: TreeMap[str, u256]
    mission_claimable: TreeMap[str, u256]
    claimable_balance: TreeMap[str, u256]
    withdrawal_count: u256
    withdrawal_exists: TreeMap[str, bool]
    withdrawal_mission: TreeMap[str, str]
    withdrawal_beneficiary: TreeMap[str, Address]
    withdrawal_amount: TreeMap[str, u256]
    withdrawal_status: TreeMap[str, str]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.mission_count = (0)
        self.withdrawal_count = (0)
        # v0.6 storage collections are allocated by the contract runtime.

    def _require_digest(self, value: str, label: str) -> None:
        if len(value) != 64:
            raise gl.vm.UserError(f"{label} must be 32-byte lowercase hex")
        for char in value:
            if char not in "0123456789abcdef":
                raise gl.vm.UserError(f"{label} must be 32-byte lowercase hex")

    def _require_uint(self, value: int, label: str, *, positive: bool = False) -> int:
        """Reject booleans and values outside the GenLayer uint256 domain."""
        if type(value) is not int or value < (1 if positive else 0) or value > MAX_U256:
            raise gl.vm.UserError(f"invalid {label}")
        return value

    def _next_uint(self, value: int, label: str) -> int:
        """Increment a stored uint only when the next value remains representable."""
        if value < 0 or value >= MAX_U256:
            raise gl.vm.UserError(f"{label} overflow")
        return value + 1

    def _require_ascii_text(self, value: str, label: str, limit: int = MAX_TEXT) -> None:
        if not value or len(value) > limit:
            raise gl.vm.UserError(f"invalid {label}")
        for char in value:
            if ord(char) < 0x20 or ord(char) > 0x7E:
                raise gl.vm.UserError(f"invalid {label}")

    def _require_mission_id(self, value: str) -> None:
        self._require_ascii_text(value, "mission id")
        if ":" in value:
            raise gl.vm.UserError("invalid mission id")

    def _require_identifier(self, value: str, label: str, limit: int) -> None:
        self._require_ascii_text(value, label, limit)
        for char in value:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_":
                raise gl.vm.UserError(f"invalid {label}")

    def _require_authority_host(self, value: str) -> None:
        self._require_ascii_text(value, "authority host", 253)
        if value != value.lower() or any(char in value for char in "/?:#@%\\"):
            raise gl.vm.UserError("invalid authority host")
        if value.startswith(".") or value.endswith(".") or ".." in value:
            raise gl.vm.UserError("invalid authority host")
        for label in value.split("."):
            if not 1 <= len(label) <= 63:
                raise gl.vm.UserError("invalid authority host")
            if label[0] == "-" or label[-1] == "-":
                raise gl.vm.UserError("invalid authority host")
            if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in label):
                raise gl.vm.UserError("invalid authority host")

    def _require_path_prefix(self, value: str) -> None:
        self._require_ascii_text(value, "authority path prefix", MAX_TEXT)
        if not value.startswith("/") or "//" in value or any(
            marker in value for marker in ("?", "#", "%", "\\")
        ):
            raise gl.vm.UserError("invalid authority path prefix")
        if value != "/" and value.endswith("/"):
            raise gl.vm.UserError("invalid authority path prefix")
        if any(segment in (".", "..") for segment in value.split("/")):
            raise gl.vm.UserError("invalid authority path prefix")

    def _url_matches_authority(self, url: str, host: str, path_prefix: str) -> bool:
        try:
            self._require_ascii_text(url, "evidence url", 2048)
        except Exception:
            return False
        origin = "https://" + host
        if not url.startswith(origin):
            return False
        remainder = url[len(origin):]
        if not remainder.startswith("/") or any(
            marker in remainder for marker in ("?", "#", "%", "\\")
        ):
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

    def _require_authority(self, authority_id: str) -> None:
        if not self.authority_exists.get(authority_id, False):
            raise gl.vm.UserError("authority not found")

    def _require_nonzero_address(self, value: gl.Address, label: str) -> None:
        if value.as_hex == "0x" + "00" * 20:
            raise gl.vm.UserError(f"{label} cannot be zero")

    def _intent_digest(
        self,
        mission_id: str,
        objective: str,
        policy_digest: str,
        budget: int,
        refund_beneficiary: gl.Address,
        prepare_deadline: int,
        recovery_deadline: int,
    ) -> str:
        fields = (
            "2",
            PROTOCOL,
            REVISION,
            str(int(gl.message.chain_id)),
            gl.message.contract_address.as_hex,
            mission_id,
            objective,
            policy_digest,
            str(budget),
            refund_beneficiary.as_hex,
            str(prepare_deadline),
            str(recovery_deadline),
        )
        payload = "commit-intent-v2" + "".join(self._frame(field) for field in fields)
        return Keccak256(payload.encode("utf-8")).hexdigest()

    @gl.public.write
    def register_authority(
        self,
        authority_id: str,
        host: str,
        path_prefix: str,
        issuer_address: gl.Address,
        authority_version: int,
    ) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("owner required")
        self._require_identifier(authority_id, "authority id", 64)
        if self.authority_exists.get(authority_id, False):
            raise gl.vm.UserError("authority already exists")
        self._require_authority_host(host)
        self._require_path_prefix(path_prefix)
        self._require_nonzero_address(issuer_address, "issuer")
        self._require_uint(
            authority_version,
            "authority version",
            positive=True,
        )
        self.authority_exists[authority_id] = True
        self.authority_active[authority_id] = True
        self.authority_host[authority_id] = host
        self.authority_path_prefix[authority_id] = path_prefix
        self.authority_issuer[authority_id] = issuer_address
        self.authority_version[authority_id] = authority_version

    @gl.public.write
    def deactivate_authority(self, authority_id: str) -> None:
        """Stop new evidence from using an authority without rewriting history."""
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("owner required")
        self._require_authority(authority_id)
        self.authority_active[authority_id] = False

    @gl.public.write
    def authorize_supplier(self, mission_id: str, supplier: gl.Address) -> None:
        """Allow one exact supplier address to prepare effects for a mission."""
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
        self._require_nonzero_address(supplier, "supplier")
        supplier_key = mission_id + ":" + supplier.as_hex
        if self.supplier_authorized.get(supplier_key, False):
            raise gl.vm.UserError("supplier already authorized")
        self.supplier_authorized[supplier_key] = True
        self.supplier_count[mission_id] = (self._next_uint(
                int(self.supplier_count.get(mission_id, (0))),
                "supplier count",
            ))

    @gl.public.write
    def revoke_supplier(self, mission_id: str, supplier: gl.Address) -> None:
        """Revoke a supplier before sealing, but never rewrite a prepared effect."""
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if supplier == self.mission_principal[mission_id]:
            raise gl.vm.UserError("principal cannot be revoked")
        supplier_key = mission_id + ":" + supplier.as_hex
        if not self.supplier_authorized.get(supplier_key, False):
            raise gl.vm.UserError("supplier is not authorized")
        for index in range(int(self.mission_effect_count[mission_id])):
            effect_key = self.mission_effect_key[mission_id + ":" + str(index)]
            if self.effect_supplier[effect_key] == supplier:
                raise gl.vm.UserError("supplier has a prepared effect")
        self.supplier_authorized[supplier_key] = False
        current_count = int(self.supplier_count.get(mission_id, (0)))
        if current_count > 0:
            self.supplier_count[mission_id] = (current_count - 1)

    def _attestation_key(
        self,
        authority_id: str,
        record_id: str,
        record_version: int,
    ) -> str:
        return authority_id + ":" + record_id + ":" + str(record_version)

    @gl.public.write
    def attest_evidence(
        self,
        authority_id: str,
        authority_version: int,
        record_id: str,
        record_version: int,
        mission_id: str,
        mission_version: int,
        url: str,
        record_hash: str,
        published_at: int,
        expires_at: int,
    ) -> None:
        self._require_authority(authority_id)
        if not self.authority_active.get(authority_id, False):
            raise gl.vm.UserError("authority is inactive")
        self._require_uint(
            authority_version,
            "authority version",
            positive=True,
        )
        if authority_version != int(self.authority_version[authority_id]):
            raise gl.vm.UserError("authority version mismatch")
        if gl.message.sender_address != self.authority_issuer[authority_id]:
            raise gl.vm.UserError("issuer required")

        self._require_identifier(record_id, "record id", MAX_TEXT)
        self._require_uint(record_version, "record version", positive=True)

        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        self._require_uint(mission_version, "mission version", positive=True)
        if mission_version != int(self.mission_version[mission_id]):
            raise gl.vm.UserError("mission version mismatch")

        if not self._url_matches_authority(
            url,
            self.authority_host[authority_id],
            self.authority_path_prefix[authority_id],
        ):
            raise gl.vm.UserError("evidence URL is outside authority")

        self._require_digest(record_hash, "record hash")
        self._require_uint(
            published_at,
            "evidence publication",
            positive=True,
        )
        self._require_uint(expires_at, "evidence expiry", positive=True)

        mission_created_at = int(self.mission_created_at[mission_id])
        if published_at < mission_created_at:
            raise gl.vm.UserError("evidence published before mission")
        if expires_at < int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("invalid evidence expiry")

        attestation_key = self._attestation_key(
            authority_id,
            record_id,
            record_version,
        )
        if self.attestation_exists.get(attestation_key, False):
            raise gl.vm.UserError("attestation already exists")

        self.attestation_exists[attestation_key] = True
        self.attestation_authority[attestation_key] = authority_id
        self.attestation_authority_version[attestation_key] = authority_version
        self.attestation_issuer[attestation_key] = gl.message.sender_address
        self.attestation_record_id[attestation_key] = record_id
        self.attestation_record_version[attestation_key] = record_version
        self.attestation_mission[attestation_key] = mission_id
        self.attestation_mission_version[attestation_key] = mission_version
        self.attestation_url[attestation_key] = url
        self.attestation_record_hash[attestation_key] = record_hash
        self.attestation_published_at[attestation_key] = published_at
        self.attestation_expires_at[attestation_key] = expires_at

    @gl.public.write
    def register_evidence(
        self,
        mission_id: str,
        evidence_id: str,
        authority_id: str,
        authority_version: int,
        record_id: str,
        record_version: int,
    ) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(
            self.mission_prepare_deadline[mission_id]
        ):
            raise gl.vm.UserError("preparation deadline has passed")

        self._require_identifier(evidence_id, "evidence id", MAX_TEXT)
        evidence_key = mission_id + ":" + evidence_id
        if self.evidence_exists.get(evidence_key, False):
            raise gl.vm.UserError("evidence already exists")

        evidence_index = int(self.mission_evidence_count[mission_id])
        if evidence_index >= MAX_EVIDENCE:
            raise gl.vm.UserError("evidence limit exceeded")

        self._require_authority(authority_id)
        self._require_uint(
            authority_version,
            "authority version",
            positive=True,
        )
        self._require_identifier(record_id, "record id", MAX_TEXT)
        self._require_uint(record_version, "record version", positive=True)

        attestation_key = self._attestation_key(
            authority_id,
            record_id,
            record_version,
        )
        if not self.attestation_exists.get(attestation_key, False):
            raise gl.vm.UserError("evidence attestation not found")

        if (
            int(self.attestation_authority_version[attestation_key])
            != authority_version
        ):
            raise gl.vm.UserError("authority version mismatch")
        if self.attestation_mission[attestation_key] != mission_id:
            raise gl.vm.UserError("attestation mission mismatch")

        current_mission_version = int(self.mission_version[mission_id])
        if (
            int(self.attestation_mission_version[attestation_key])
            != current_mission_version
        ):
            raise gl.vm.UserError("attestation mission version mismatch")

        self.evidence_exists[evidence_key] = True
        self.evidence_mission[evidence_key] = mission_id
        self.evidence_id[evidence_key] = evidence_id
        self.evidence_authority[evidence_key] = authority_id
        self.evidence_authority_version[evidence_key] = authority_version
        self.evidence_issuer[evidence_key] = self.attestation_issuer[attestation_key]
        self.evidence_record_id[evidence_key] = record_id
        self.evidence_record_version[evidence_key] = record_version
        self.evidence_mission_version[evidence_key] = current_mission_version
        self.evidence_url[evidence_key] = self.attestation_url[attestation_key]
        self.evidence_record_hash[evidence_key] = (
            self.attestation_record_hash[attestation_key]
        )
        self.evidence_subject[evidence_key] = mission_id
        self.evidence_published_at[evidence_key] = (
            self.attestation_published_at[attestation_key]
        )
        self.evidence_expires_at[evidence_key] = (
            self.attestation_expires_at[attestation_key]
        )
        self.mission_evidence_key[
            mission_id + ":" + str(evidence_index)
        ] = evidence_key
        self.mission_evidence_count[mission_id] = self._next_uint(
            evidence_index,
            "evidence count",
        )

    @gl.public.write
    def create_mission(
        self,
        mission_id: str,
        objective: str,
        policy_digest: str,
        budget: int,
        refund_beneficiary: gl.Address,
        prepare_deadline: int,
        recovery_deadline: int,
    ) -> None:
        self._require_mission_id(mission_id)
        self._require_ascii_text(objective, "objective")
        self._require_digest(policy_digest, "policy digest")
        self._require_uint(budget, "mission budget", positive=True)
        self._require_uint(prepare_deadline, "preparation deadline", positive=True)
        self._require_uint(recovery_deadline, "recovery deadline", positive=True)
        if policy_digest != POLICY_DIGEST:
            raise gl.vm.UserError("unsupported policy rule")
        if self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission already exists")
        self._require_nonzero_address(refund_beneficiary, "refund beneficiary")
        if recovery_deadline <= prepare_deadline:
            raise gl.vm.UserError("invalid deadline order")

        self.mission_exists[mission_id] = True
        self.mission_principal[mission_id] = gl.message.sender_address
        self.mission_state[mission_id] = STATE_PREPARING
        self.mission_objective[mission_id] = objective
        self.mission_policy_digest[mission_id] = policy_digest
        self.mission_intent_digest[mission_id] = self._intent_digest(
            mission_id,
            objective,
            policy_digest,
            budget,
            refund_beneficiary,
            prepare_deadline,
            recovery_deadline,
        )
        self.mission_effect_root[mission_id] = ""
        self.mission_evidence_root[mission_id] = ""
        self.mission_budget[mission_id] = (budget)
        self.mission_funded_value[mission_id] = (0)
        self.mission_prepared_value[mission_id] = (0)
        self.mission_refund_beneficiary[mission_id] = refund_beneficiary
        self.mission_refund_entitlement[mission_id] = (0)
        self.mission_decision_nonce[mission_id] = ""
        self.mission_allocation_applied[mission_id] = False
        self.mission_evidence_count[mission_id] = (0)
        self.mission_decision[mission_id] = ""
        self.mission_reason_code[mission_id] = ""
        self.mission_evaluation_count[mission_id] = (0)
        self.mission_prepare_deadline[mission_id] = (prepare_deadline)
        self.mission_recovery_deadline[mission_id] = (recovery_deadline)
        self.mission_created_at[mission_id] = int(
            datetime.now(timezone.utc).timestamp()
        )
        self.mission_version[mission_id] = (1)
        self.mission_effect_count[mission_id] = (0)
        # The principal may prepare its own effects. Other participants must
        # be explicitly authorized before they can contribute any effect.
        self.supplier_authorized[mission_id + ":" + gl.message.sender_address.as_hex] = True
        self.supplier_count[mission_id] = (1)
        mission_index = int(self.mission_count)
        self.mission_key[str(mission_index)] = mission_id
        self.mission_count = (self._next_uint(mission_index, "mission count"))

    @gl.public.write.payable
    def fund_mission(self, mission_id: str) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
        amount = int(gl.message.value)
        if amount <= 0:
            raise gl.vm.UserError("funding value must be positive")
        funded = int(self.mission_funded_value[mission_id])
        if funded + amount > int(self.mission_budget[mission_id]):
            raise gl.vm.UserError("funding exceeds mission budget")
        self.mission_funded_value[mission_id] = (funded + amount)

    @gl.public.write
    def prepare_effect(
        self,
        mission_id: str,
        effect_id: str,
        effect_digest: str,
        beneficiary: gl.Address,
        value: int,
        expiry: int,
    ) -> None:
        self._prepare_effect(
            mission_id, effect_id, effect_digest, beneficiary, value, expiry, ""
        )

    @gl.public.write
    def prepare_effect_with_dependency(
        self,
        mission_id: str,
        effect_id: str,
        effect_digest: str,
        beneficiary: gl.Address,
        value: int,
        expiry: int,
        dependency_id: str,
    ) -> None:
        """Prepare an effect and bind it to an earlier effect in this mission."""
        self._prepare_effect(
            mission_id, effect_id, effect_digest, beneficiary, value, expiry, dependency_id
        )

    def _prepare_effect(
        self,
        mission_id: str,
        effect_id: str,
        effect_digest: str,
        beneficiary: gl.Address,
        value: int,
        expiry: int,
        dependency_id: str,
    ) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
        self._require_uint(value, "effect value", positive=True)
        self._require_uint(expiry, "effect expiry", positive=True)
        supplier_key = mission_id + ":" + gl.message.sender_address.as_hex
        if not self.supplier_authorized.get(supplier_key, False):
            raise gl.vm.UserError("supplier is not authorized")
        if not effect_id or len(effect_id) > MAX_TEXT or ":" in effect_id:
            raise gl.vm.UserError("invalid effect id")
        self._require_ascii_text(effect_id, "effect id")
        effect_key = mission_id + ":" + effect_id
        if self.effect_exists.get(effect_key, False):
            raise gl.vm.UserError("effect already exists")
        effect_index = int(self.mission_effect_count[mission_id])
        if effect_index >= MAX_EFFECTS:
            raise gl.vm.UserError("effect limit exceeded")
        self._require_digest(effect_digest, "effect digest")
        if dependency_id:
            self._require_identifier(dependency_id, "dependency id", MAX_TEXT)
            if dependency_id == effect_id:
                raise gl.vm.UserError("effect cannot depend on itself")
            dependency_key = mission_id + ":" + dependency_id
            if not self.effect_exists.get(dependency_key, False):
                raise gl.vm.UserError("dependency effect not found")
        self._require_nonzero_address(beneficiary, "effect beneficiary")
        if int(self.mission_prepared_value[mission_id]) + value > int(self.mission_budget[mission_id]):
            raise gl.vm.UserError("prepared effects exceed mission budget")
        if expiry < int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("invalid effect expiry")

        self.effect_exists[effect_key] = True
        self.effect_mission[effect_key] = mission_id
        self.effect_supplier[effect_key] = gl.message.sender_address
        self.effect_id[effect_key] = effect_id
        self.effect_digest[effect_key] = effect_digest
        self.effect_parent[effect_key] = dependency_id
        self.effect_beneficiary[effect_key] = beneficiary
        self.effect_value[effect_key] = (value)
        self.effect_expiry[effect_key] = (expiry)
        self.mission_prepared_value[mission_id] = (int(self.mission_prepared_value[mission_id]) + value)
        self.mission_effect_key[mission_id + ":" + str(effect_index)] = effect_key
        self.mission_effect_count[mission_id] = (self._next_uint(effect_index, "effect count"))

    @gl.public.write
    def seal_mission(self, mission_id: str, effect_root: str, evidence_root: str) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
        if self.mission_effect_count[mission_id] <= 0:
            raise gl.vm.UserError("mission has no prepared effects")
        if self.mission_evidence_count[mission_id] < 2:
            raise gl.vm.UserError("mission needs two evidence records")
        if self.mission_funded_value[mission_id] < self.mission_prepared_value[mission_id]:
            raise gl.vm.UserError("mission is underfunded")
        if not self._has_distinct_evidence_authorities(mission_id):
            raise gl.vm.UserError("evidence authorities must be distinct")
        self._require_acyclic_effect_graph(mission_id)
        self._require_digest(effect_root, "effect root")
        self._require_digest(evidence_root, "evidence root")
        if effect_root != self.derive_effect_root(mission_id):
            raise gl.vm.UserError("effect root does not match prepared effects")
        if evidence_root != self.derive_evidence_root(mission_id):
            raise gl.vm.UserError("evidence root does not match registered evidence")
        self.mission_effect_root[mission_id] = effect_root
        self.mission_evidence_root[mission_id] = evidence_root
        self.mission_state[mission_id] = STATE_SEALED

    @gl.public.write
    def cancel_mission(self, mission_id: str) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("sealed mission cannot be cancelled")
        self._allocate_abort(mission_id, "cancelled_by_principal")

    @gl.public.write
    def evaluate_mission(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        # Evaluation is permissionless after sealing so a principal going
        # offline cannot strand a mission before its recovery deadline.
        if self.mission_state[mission_id] != STATE_SEALED:
            raise gl.vm.UserError("mission is not sealed")
        if self.mission_decision[mission_id]:
            raise gl.vm.UserError("mission already evaluated")
        now = int(datetime.now(timezone.utc).timestamp())
        if now >= int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("recovery deadline has passed")

        # Read all deterministic storage before entering nondeterministic code.
        # GenLayer does not make contract storage available inside leader_fn or
        # validator_fn, so the closures capture an immutable source manifest.
        source_specs = []
        for index in range(int(self.mission_evidence_count[mission_id])):
            evidence_key = self.mission_evidence_key[mission_id + ":" + str(index)]
            source_specs.append((
                self.evidence_id[evidence_key],
                self.evidence_authority[evidence_key],
                self.evidence_url[evidence_key],
                self.evidence_record_hash[evidence_key],
                int(self.evidence_expires_at[evidence_key]),
            ))
        mission_id_snapshot = mission_id
        objective_snapshot = self.mission_objective[mission_id]
        policy_digest_snapshot = self.mission_policy_digest[mission_id]
        intent_digest_snapshot = self.mission_intent_digest[mission_id]
        effect_root_snapshot = self.mission_effect_root[mission_id]
        evidence_root_snapshot = self.mission_evidence_root[mission_id]
        effect_specs = []
        for index in range(int(self.mission_effect_count[mission_id])):
            effect_key = self.mission_effect_key[mission_id + ":" + str(index)]
            effect_specs.append((
                self.effect_id[effect_key],
                self.effect_parent.get(effect_key, ""),
                self.effect_digest[effect_key],
                self.effect_beneficiary[effect_key].as_hex,
                int(self.effect_value[effect_key]),
                int(self.effect_expiry[effect_key]),
            ))

        def leader_fn() -> dict:
            all_eligible = True
            for evidence_id, authority_id, url, expected_hash, expected_expiry in source_specs:
                response = gl.nondet.web.get(url)
                if response.status != 200:
                    raise gl.vm.UserError("evidence source unavailable")
                if not isinstance(response.body, bytes):
                    raise gl.vm.UserError("evidence response body missing")
                if len(response.body) > MAX_REMOTE_BODY:
                    raise gl.vm.UserError("evidence record is too large")

                def reject_duplicate_keys(pairs):
                    parsed = {}
                    for key, value in pairs:
                        if key in parsed:
                            raise gl.vm.UserError("duplicate evidence key")
                        parsed[key] = value
                    return parsed

                def reject_nonstandard_number(value):
                    raise gl.vm.UserError("invalid evidence JSON")

                try:
                    record = json.loads(
                        response.body.decode("utf-8"),
                        object_pairs_hook=reject_duplicate_keys,
                        parse_constant=reject_nonstandard_number,
                    )
                except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                    raise gl.vm.UserError("invalid evidence JSON")
                if not isinstance(record, dict):
                    raise gl.vm.UserError("evidence record must be an object")
                if record.get("schema") != EVIDENCE_SCHEMA:
                    raise gl.vm.UserError("unsupported evidence schema")
                expected_record_keys = {
                    "schema", "evidence_id", "authority_id", "url", "subject",
                    "expires_at", "mission_id", "objective", "policy_digest",
                    "policy_rule", "intent_digest", "effect_root", "payload",
                }
                if set(record.keys()) != expected_record_keys:
                    raise gl.vm.UserError("unsupported evidence record")
                if record.get("evidence_id") != evidence_id:
                    raise gl.vm.UserError("evidence id mismatch")
                if record.get("authority_id") != authority_id:
                    raise gl.vm.UserError("evidence authority mismatch")
                if record.get("url") != url:
                    raise gl.vm.UserError("evidence URL mismatch")
                if record.get("subject") != mission_id_snapshot:
                    raise gl.vm.UserError("evidence subject mismatch")
                if type(record.get("expires_at")) is not int:
                    raise gl.vm.UserError("evidence expiry missing")
                if record.get("expires_at") != int(expected_expiry):
                    raise gl.vm.UserError("evidence expiry mismatch")
                if record.get("mission_id") != mission_id_snapshot:
                    raise gl.vm.UserError("evidence mission mismatch")
                if record.get("objective") != objective_snapshot:
                    raise gl.vm.UserError("evidence objective mismatch")
                if record.get("policy_digest") != policy_digest_snapshot:
                    raise gl.vm.UserError("evidence policy mismatch")
                if record.get("policy_rule") != POLICY_RULE:
                    raise gl.vm.UserError("evidence policy rule mismatch")
                if record.get("intent_digest") != intent_digest_snapshot:
                    raise gl.vm.UserError("evidence intent mismatch")
                if record.get("effect_root") != effect_root_snapshot:
                    raise gl.vm.UserError("evidence effect root mismatch")
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    raise gl.vm.UserError("evidence payload must be an object")
                if set(payload.keys()) != {"eligible", "reason_code", "effect_claims"}:
                    raise gl.vm.UserError("unsupported evidence payload")
                if type(payload.get("eligible")) is not bool:
                    raise gl.vm.UserError("evidence eligibility missing")
                if type(payload.get("reason_code")) is not str or not payload["reason_code"]:
                    raise gl.vm.UserError("evidence reason missing")
                reason_code = payload["reason_code"]
                if len(reason_code) > MAX_REASON or any(
                    ord(char) < 0x20 or ord(char) > 0x7E for char in reason_code
                ):
                    raise gl.vm.UserError("evidence reason is invalid")
                effect_claims = payload.get("effect_claims")
                if not isinstance(effect_claims, dict):
                    raise gl.vm.UserError("effect claims must be an object")
                expected_effect_ids = {spec[0] for spec in effect_specs}
                if set(effect_claims.keys()) != expected_effect_ids:
                    raise gl.vm.UserError("effect claims do not match sealed effects")
                all_effects_eligible = True
                for effect_id, _parent, _digest, _beneficiary, _value, _expiry in effect_specs:
                    if type(effect_claims.get(effect_id)) is not bool:
                        raise gl.vm.UserError("effect claim must be boolean")
                    if not effect_claims[effect_id]:
                        all_effects_eligible = False
                canonical_payload = json.dumps(
                    payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                )
                computed_hash = Keccak256(canonical_payload.encode("utf-8")).hexdigest()
                if computed_hash != expected_hash:
                    raise gl.vm.UserError("evidence payload hash mismatch")
                if not payload["eligible"] or not all_effects_eligible:
                    all_eligible = False
            return {
                "decision": "COMMIT" if all_eligible else "ABORT",
                "reason_code": (
                    "all_sources_and_effects_eligible"
                    if all_eligible else "policy_or_source_ineligible"
                ),
                "mission_id": mission_id_snapshot,
                "revision": REVISION,
                "intent_digest": intent_digest_snapshot,
                "policy_digest": policy_digest_snapshot,
                "policy_rule": POLICY_RULE,
                "effect_root": effect_root_snapshot,
                "evidence_root": evidence_root_snapshot,
                "effect_count": len(effect_specs),
                "evidence_count": len(source_specs),
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_data = leader_fn()
            except Exception:
                return False
            leader_data = leader_result.calldata
            if not isinstance(leader_data, dict):
                return False
            return (
                leader_data.get("decision") == validator_data["decision"]
                and leader_data.get("reason_code") == validator_data["reason_code"]
                and leader_data.get("mission_id") == validator_data["mission_id"]
                and leader_data.get("revision") == validator_data["revision"]
                and leader_data.get("intent_digest") == validator_data["intent_digest"]
                and leader_data.get("policy_digest") == validator_data["policy_digest"]
                and leader_data.get("policy_rule") == validator_data["policy_rule"]
                and leader_data.get("effect_root") == validator_data["effect_root"]
                and leader_data.get("evidence_root") == validator_data["evidence_root"]
                and leader_data.get("effect_count") == validator_data["effect_count"]
                and leader_data.get("evidence_count") == validator_data["evidence_count"]
            )

        # The pinned Studio Dev v0.6 stack and its linter expose run_nondet as
        # the compatible custom-validator primitive. validator_fn catches its
        # own errors and returns False, so disagreement cannot mutate state.
        result = gl.vm.run_nondet(leader_fn, validator_fn)
        if result["decision"] not in ("COMMIT", "ABORT"):
            raise gl.vm.UserError("invalid consensus decision")
        self.mission_decision[mission_id] = result["decision"]
        self.mission_reason_code[mission_id] = result["reason_code"]
        self.mission_evaluation_count[mission_id] = (self._next_uint(
                int(self.mission_evaluation_count[mission_id]),
                "evaluation count",
            ))
        decision_nonce = Keccak256(
            (
                DECISION_ENVELOPE
                + self._frame(mission_id)
                + self._frame(str(int(self.mission_version[mission_id])))
                + self._frame(result["decision"])
                + self._frame(result["reason_code"])
                + self._frame(self.mission_effect_root[mission_id])
                + self._frame(self.mission_evidence_root[mission_id])
            ).encode("utf-8")
        ).hexdigest()
        self.mission_decision_nonce[mission_id] = decision_nonce
        self.mission_state[mission_id] = STATE_DECISION_PENDING
        _get_contract_at(gl.message.contract_address).emit(on="finalized").apply_decision(
            mission_id, decision_nonce
        )

    @gl.public.write
    def apply_decision(self, mission_id: str, decision_nonce: str) -> None:
        if gl.message.sender_address != gl.message.contract_address:
            raise gl.vm.UserError("self message required")
        # A recovery transaction may win the race after the parent decision
        # was produced. A late authenticated callback must be harmless.
        if self.mission_allocation_applied[mission_id]:
            return
        if decision_nonce != self.mission_decision_nonce[mission_id]:
            raise gl.vm.UserError("decision nonce mismatch")
        if self.mission_state[mission_id] != STATE_DECISION_PENDING:
            raise gl.vm.UserError("decision is not pending")
        if self.mission_decision[mission_id] == "COMMIT":
            self._allocate_commit(mission_id)
        elif self.mission_decision[mission_id] == "ABORT":
            self._allocate_abort(mission_id, self.mission_reason_code[mission_id])
        else:
            raise gl.vm.UserError("invalid decision")

    @gl.public.write
    def claim_mission(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if self.mission_state[mission_id] not in (STATE_COMMITTED, STATE_ABORTED):
            raise gl.vm.UserError("mission is not allocated")
        beneficiary = gl.message.sender_address
        claim_key = mission_id + ":" + beneficiary.as_hex
        amount = int(self.mission_claimable.get(claim_key, (0)))
        if amount <= 0:
            raise gl.vm.UserError("no claimable balance")
        withdrawal_id = str(int(self.withdrawal_count))
        if self.withdrawal_exists.get(withdrawal_id, False):
            raise gl.vm.UserError("withdrawal id collision")
        self.mission_claimable[claim_key] = (0)
        global_key = beneficiary.as_hex
        current_global = int(self.claimable_balance.get(global_key, (0)))
        if current_global < amount:
            raise gl.vm.UserError("claimable balance underflow")
        self.claimable_balance[global_key] = (current_global - amount)
        self.withdrawal_exists[withdrawal_id] = True
        self.withdrawal_mission[withdrawal_id] = mission_id
        self.withdrawal_beneficiary[withdrawal_id] = beneficiary
        self.withdrawal_amount[withdrawal_id] = (amount)
        self.withdrawal_status[withdrawal_id] = WITHDRAWAL_DISPATCHED
        self.withdrawal_count = (self._next_uint(int(self.withdrawal_count), "withdrawal count"))
        # External GEN transfers are finalized child messages. The entitlement
        # is consumed before dispatch and is never retried without a verified
        # delivery/non-delivery proof, preventing double payment.
        _NativeRecipient(beneficiary).emit_transfer(value=amount)

    @gl.public.write
    def expire_mission(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if self.mission_state[mission_id] not in (
            STATE_PREPARING, STATE_SEALED, STATE_DECISION_PENDING
        ):
            raise gl.vm.UserError("mission is already terminal")
        now = int(datetime.now(timezone.utc).timestamp())
        if now < int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("recovery deadline has not passed")
        self._allocate_abort(mission_id, "recovery_deadline_expired")

    @gl.public.view
    def protocol_info(self) -> dict:
        return {
            "protocol": PROTOCOL,
            "revision": REVISION,
            "custody_enabled": True,
            "semantic_evaluation_enabled": True,
            "equivalence_primitive": "run_nondet",
            "decision_envelope": DECISION_ENVELOPE,
            "receipt_schema": RECEIPT_SCHEMA,
            "manifest_schema": MANIFEST_SCHEMA,
            "evaluation_trigger": "permissionless-after-seal",
            "authority_provenance": "https-origin-path",
            "mission_count": int(self.mission_count),
            "external_withdrawal_recovery": False,
            "supplier_authorization_required": True,
            "effect_graph": "single-parent-acyclic",
            "evidence_schema": EVIDENCE_SCHEMA,
            "policy_rule": POLICY_RULE,
            "policy_digest": POLICY_DIGEST,
            "remote_body_limit": MAX_REMOTE_BODY,
        }

    @gl.public.view
    def get_claimable(self, beneficiary: gl.Address) -> int:
        return int(self.claimable_balance.get(beneficiary.as_hex, (0)))

    @gl.public.view
    def get_mission_claimable(self, mission_id: str, beneficiary: gl.Address) -> int:
        """Return only this beneficiary's entitlement for this mission."""
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return int(
            self.mission_claimable.get(
                mission_id + ":" + beneficiary.as_hex, (0)
            )
        )

    @gl.public.view
    def get_mission_receipt(self, mission_id: str) -> dict:
        """Return one auditable proof envelope for clients and reviewers."""
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return {
            "receipt_schema": RECEIPT_SCHEMA,
            "manifest_schema": MANIFEST_SCHEMA,
            "protocol": PROTOCOL,
            "revision": REVISION,
            "chain_id": int(gl.message.chain_id),
            "coordinator": gl.message.contract_address.as_hex,
            "mission_id": mission_id,
            "principal": self.mission_principal[mission_id].as_hex,
            "version": int(self.mission_version[mission_id]),
            "objective": self.mission_objective[mission_id],
            "state": self.mission_state[mission_id],
            "decision": self.mission_decision[mission_id],
            "reason_code": self.mission_reason_code[mission_id],
            "decision_nonce": self.mission_decision_nonce[mission_id],
            "policy_rule": POLICY_RULE,
            "policy_digest": self.mission_policy_digest[mission_id],
            "intent_digest": self.mission_intent_digest[mission_id],
            "effect_root": self.mission_effect_root[mission_id],
            "evidence_root": self.mission_evidence_root[mission_id],
            "effect_count": int(self.mission_effect_count[mission_id]),
            "evidence_count": int(self.mission_evidence_count[mission_id]),
            "budget": int(self.mission_budget[mission_id]),
            "funded_value": int(self.mission_funded_value[mission_id]),
            "prepared_value": int(self.mission_prepared_value[mission_id]),
            "refund_beneficiary": self.mission_refund_beneficiary[mission_id].as_hex,
            "refund_entitlement": int(self.mission_refund_entitlement[mission_id]),
            "prepare_deadline": int(self.mission_prepare_deadline[mission_id]),
            "recovery_deadline": int(self.mission_recovery_deadline[mission_id]),
            "evaluation_count": int(self.mission_evaluation_count[mission_id]),
            "allocation_applied": self.mission_allocation_applied[mission_id],
            "external_withdrawal_recovery": False,
        }

    @gl.public.view
    def get_withdrawal(self, withdrawal_id: str) -> dict:
        if not self.withdrawal_exists.get(withdrawal_id, False):
            raise gl.vm.UserError("withdrawal not found")
        return {
            "withdrawal_id": withdrawal_id,
            "mission_id": self.withdrawal_mission[withdrawal_id],
            "beneficiary": self.withdrawal_beneficiary[withdrawal_id].as_hex,
            "amount": int(self.withdrawal_amount[withdrawal_id]),
            "status": self.withdrawal_status[withdrawal_id],
        }

    @gl.public.view
    def get_withdrawal_count(self) -> int:
        return int(self.withdrawal_count)

    @gl.public.view
    def get_withdrawal_by_index(self, index: int) -> dict:
        if index < 0 or index >= int(self.withdrawal_count):
            raise gl.vm.UserError("withdrawal index out of range")
        return self.get_withdrawal(str(index))

    @gl.public.view
    def derive_intent_digest(self, mission_id: str) -> str:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return self._intent_digest(
            mission_id,
            self.mission_objective[mission_id],
            self.mission_policy_digest[mission_id],
            int(self.mission_budget[mission_id]),
            self.mission_refund_beneficiary[mission_id],
            int(self.mission_prepare_deadline[mission_id]),
            int(self.mission_recovery_deadline[mission_id]),
        )

    def _require_principal(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if gl.message.sender_address != self.mission_principal[mission_id]:
            raise gl.vm.UserError("principal required")

    def _credit_claimable(self, mission_id: str, beneficiary: gl.Address, amount: int) -> None:
        if amount <= 0:
            return
        claim_key = mission_id + ":" + beneficiary.as_hex
        mission_current = int(self.mission_claimable.get(claim_key, (0)))
        global_key = beneficiary.as_hex
        global_current = int(self.claimable_balance.get(global_key, (0)))
        if amount > MAX_U256 - mission_current:
            raise gl.vm.UserError("mission claimable balance overflow")
        if amount > MAX_U256 - global_current:
            raise gl.vm.UserError("global claimable balance overflow")
        self.mission_claimable[claim_key] = (mission_current + amount)
        self.claimable_balance[global_key] = (global_current + amount)

    def _allocate_commit(self, mission_id: str) -> None:
        funded = int(self.mission_funded_value[mission_id])
        prepared = int(self.mission_prepared_value[mission_id])
        if funded < prepared:
            raise gl.vm.UserError("mission is underfunded")
        for index in range(int(self.mission_effect_count[mission_id])):
            effect_key = self.mission_effect_key[mission_id + ":" + str(index)]
            amount = int(self.effect_value[effect_key])
            self._credit_claimable(
                mission_id, self.effect_beneficiary[effect_key], amount
            )
        refund = funded - prepared
        self.mission_refund_entitlement[mission_id] = (refund)
        self._credit_claimable(
            mission_id, self.mission_refund_beneficiary[mission_id], refund
        )
        self.mission_allocation_applied[mission_id] = True
        self.mission_state[mission_id] = STATE_COMMITTED

    def _allocate_abort(self, mission_id: str, reason_code: str) -> None:
        if self.mission_allocation_applied[mission_id]:
            return
        funded = int(self.mission_funded_value[mission_id])
        # Deterministic cancellation and timeout are still explicit ABORT
        # decisions. This also invalidates any unresolved COMMIT callback that
        # races with recovery, so the public receipt cannot lie about outcome.
        self.mission_decision[mission_id] = "ABORT"
        self.mission_reason_code[mission_id] = reason_code
        self.mission_refund_entitlement[mission_id] = (funded)
        self._credit_claimable(
            mission_id, self.mission_refund_beneficiary[mission_id], funded
        )
        self.mission_allocation_applied[mission_id] = True
        self.mission_state[mission_id] = STATE_ABORTED

    def _has_distinct_evidence_authorities(self, mission_id: str) -> bool:
        first_key = self.mission_evidence_key[mission_id + ":0"]
        first_issuer = self.evidence_issuer[first_key]
        count = int(self.mission_evidence_count[mission_id])
        for index in range(1, count):
            key = self.mission_evidence_key[mission_id + ":" + str(index)]
            if self.evidence_issuer[key] != first_issuer:
                return True
        return False

    def _require_acyclic_effect_graph(self, mission_id: str) -> None:
        """Validate the bounded single-parent effect graph before sealing."""
        count = int(self.mission_effect_count[mission_id])
        for index in range(count):
            current_key = self.mission_effect_key[mission_id + ":" + str(index)]
            visited = 0
            while True:
                parent_id = self.effect_parent.get(current_key, "")
                if not parent_id:
                    break
                parent_key = mission_id + ":" + parent_id
                if not self.effect_exists.get(parent_key, False):
                    raise gl.vm.UserError("dependency effect not found")
                if self.effect_mission[parent_key] != mission_id:
                    raise gl.vm.UserError("dependency mission mismatch")
                visited += 1
                if visited >= count:
                    raise gl.vm.UserError("effect graph contains a cycle")
                current_key = parent_key

    def _frame(self, value: str) -> str:
        return str(len(value)) + ":" + value

    def _effect_leaf(self, effect_key: str) -> str:
        fields = (
            self.effect_id[effect_key],
            self.effect_digest[effect_key],
            self.effect_parent.get(effect_key, ""),
            self.effect_supplier[effect_key].as_hex,
            self.effect_beneficiary[effect_key].as_hex,
            str(int(self.effect_value[effect_key])),
            str(int(self.effect_expiry[effect_key])),
        )
        payload = "commit-effect-leaf-v1" + "".join(self._frame(field) for field in fields)
        return Keccak256(payload.encode("utf-8")).hexdigest()

    def _evidence_leaf(self, evidence_key: str) -> str:
        fields = (
            self.evidence_id[evidence_key],
            self.evidence_authority[evidence_key],
            str(int(self.evidence_authority_version[evidence_key])),
            self.evidence_issuer[evidence_key].as_hex,
            self.evidence_record_id[evidence_key],
            str(int(self.evidence_record_version[evidence_key])),
            self.evidence_mission[evidence_key],
            str(int(self.evidence_mission_version[evidence_key])),
            self.evidence_url[evidence_key],
            self.evidence_record_hash[evidence_key],
            self.evidence_subject[evidence_key],
            str(int(self.evidence_published_at[evidence_key])),
            str(int(self.evidence_expires_at[evidence_key])),
        )
        payload = "commit-evidence-leaf-v2" + "".join(
            self._frame(field) for field in fields
        )
        return Keccak256(payload.encode("utf-8")).hexdigest()

    @gl.public.view
    def derive_effect_root(self, mission_id: str) -> str:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        count = int(self.mission_effect_count[mission_id])
        payload = "commit-effect-root-v1" + self._frame(str(count))
        for index in range(count):
            effect_key = self.mission_effect_key[mission_id + ":" + str(index)]
            payload += self._frame(self._effect_leaf(effect_key))
        return Keccak256(payload.encode("utf-8")).hexdigest()

    @gl.public.view
    def derive_evidence_root(self, mission_id: str) -> str:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        count = int(self.mission_evidence_count[mission_id])
        payload = "commit-evidence-root-v2" + self._frame(str(count))
        for index in range(count):
            evidence_key = self.mission_evidence_key[mission_id + ":" + str(index)]
            payload += self._frame(self._evidence_leaf(evidence_key))
        return Keccak256(payload.encode("utf-8")).hexdigest()

    @gl.public.view
    def get_mission(self, mission_id: str) -> dict:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return {
            "mission_id": mission_id,
            "principal": self.mission_principal[mission_id].as_hex,
            "state": self.mission_state[mission_id],
            "version": int(self.mission_version[mission_id]),
            "objective": self.mission_objective[mission_id],
            "policy_digest": self.mission_policy_digest[mission_id],
            "intent_digest": self.mission_intent_digest[mission_id],
            "effect_root": self.mission_effect_root[mission_id],
            "evidence_root": self.mission_evidence_root[mission_id],
            "policy_rule": POLICY_RULE,
            "budget": int(self.mission_budget[mission_id]),
            "funded_value": int(self.mission_funded_value[mission_id]),
            "prepared_value": int(self.mission_prepared_value[mission_id]),
            "refund_beneficiary": self.mission_refund_beneficiary[mission_id].as_hex,
            "effect_count": int(self.mission_effect_count[mission_id]),
            "evidence_count": int(self.mission_evidence_count[mission_id]),
            "supplier_count": int(self.supplier_count.get(mission_id, (0))),
            "decision": self.mission_decision[mission_id],
            "reason_code": self.mission_reason_code[mission_id],
            "decision_nonce": self.mission_decision_nonce[mission_id],
            "allocation_applied": self.mission_allocation_applied[mission_id],
            "refund_entitlement": int(self.mission_refund_entitlement[mission_id]),
            "evaluation_count": int(self.mission_evaluation_count[mission_id]),
            "prepare_deadline": int(self.mission_prepare_deadline[mission_id]),
            "recovery_deadline": int(self.mission_recovery_deadline[mission_id]),
            "created_at": int(self.mission_created_at[mission_id]),
        }

    @gl.public.view
    def get_mission_by_index(self, index: int) -> dict:
        if index < 0 or index >= int(self.mission_count):
            raise gl.vm.UserError("mission index out of range")
        return self.get_mission(self.mission_key[str(index)])

    @gl.public.view
    def get_effect(self, mission_id: str, effect_id: str) -> dict:
        effect_key = mission_id + ":" + effect_id
        if not self.effect_exists.get(effect_key, False):
            raise gl.vm.UserError("effect not found")
        if self.effect_mission[effect_key] != mission_id:
            raise gl.vm.UserError("effect mission mismatch")
        return {
            "mission_id": mission_id,
            "effect_id": effect_id,
            "supplier": self.effect_supplier[effect_key].as_hex,
            "digest": self.effect_digest[effect_key],
            "dependency_id": self.effect_parent.get(effect_key, ""),
            "beneficiary": self.effect_beneficiary[effect_key].as_hex,
            "value": int(self.effect_value[effect_key]),
            "expiry": int(self.effect_expiry[effect_key]),
        }

    @gl.public.view
    def get_effect_by_index(self, mission_id: str, index: int) -> dict:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if index < 0 or index >= int(self.mission_effect_count[mission_id]):
            raise gl.vm.UserError("effect index out of range")
        effect_key = self.mission_effect_key[mission_id + ":" + str(index)]
        return self.get_effect(mission_id, self.effect_id[effect_key])

    @gl.public.view
    def get_authority(self, authority_id: str) -> dict:
        self._require_authority(authority_id)
        return {
            "authority_id": authority_id,
            "active": self.authority_active.get(authority_id, False),
            "host": self.authority_host[authority_id],
            "path_prefix": self.authority_path_prefix[authority_id],
            "issuer_address": self.authority_issuer[authority_id],
            "authority_version": int(self.authority_version[authority_id]),
        }

    @gl.public.view
    def authorities_are_independent(
        self,
        authority_a: str,
        authority_b: str,
    ) -> bool:
        self._require_authority(authority_a)
        self._require_authority(authority_b)
        if authority_a == authority_b:
            return False
        return self.authority_issuer[authority_a] != self.authority_issuer[authority_b]

    @gl.public.view
    def get_evidence_attestation(
        self,
        authority_id: str,
        record_id: str,
        record_version: int,
    ) -> dict:
        self._require_authority(authority_id)
        self._require_identifier(record_id, "record id", MAX_TEXT)
        self._require_uint(record_version, "record version", positive=True)

        attestation_key = self._attestation_key(
            authority_id,
            record_id,
            record_version,
        )
        if not self.attestation_exists.get(attestation_key, False):
            raise gl.vm.UserError("evidence attestation not found")

        return {
            "authority_id": self.attestation_authority[attestation_key],
            "authority_version": int(
                self.attestation_authority_version[attestation_key]
            ),
            "issuer_address": self.attestation_issuer[attestation_key],
            "record_id": self.attestation_record_id[attestation_key],
            "record_version": int(
                self.attestation_record_version[attestation_key]
            ),
            "mission_id": self.attestation_mission[attestation_key],
            "mission_version": int(
                self.attestation_mission_version[attestation_key]
            ),
            "url": self.attestation_url[attestation_key],
            "record_hash": self.attestation_record_hash[attestation_key],
            "published_at": int(
                self.attestation_published_at[attestation_key]
            ),
            "expires_at": int(
                self.attestation_expires_at[attestation_key]
            ),
        }

    @gl.public.view
    def get_evidence(self, mission_id: str, evidence_id: str) -> dict:
        evidence_key = mission_id + ":" + evidence_id
        if not self.evidence_exists.get(evidence_key, False):
            raise gl.vm.UserError("evidence not found")
        if self.evidence_mission[evidence_key] != mission_id:
            raise gl.vm.UserError("evidence mission mismatch")
        return {
            "mission_id": mission_id,
            "evidence_id": evidence_id,
            "authority_id": self.evidence_authority[evidence_key],
            "authority_version": int(
                self.evidence_authority_version[evidence_key]
            ),
            "issuer_address": self.evidence_issuer[evidence_key],
            "record_id": self.evidence_record_id[evidence_key],
            "record_version": int(
                self.evidence_record_version[evidence_key]
            ),
            "mission_version": int(
                self.evidence_mission_version[evidence_key]
            ),
            "url": self.evidence_url[evidence_key],
            "record_hash": self.evidence_record_hash[evidence_key],
            "subject": self.evidence_subject[evidence_key],
            "published_at": int(
                self.evidence_published_at[evidence_key]
            ),
            "expires_at": int(self.evidence_expires_at[evidence_key]),
        }

    @gl.public.view
    def get_evidence_by_index(self, mission_id: str, index: int) -> dict:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if index < 0 or index >= int(self.mission_evidence_count[mission_id]):
            raise gl.vm.UserError("evidence index out of range")
        evidence_key = self.mission_evidence_key[mission_id + ":" + str(index)]
        return self.get_evidence(mission_id, self.evidence_id[evidence_key])

    @gl.public.view
    def get_mission_manifest(self, mission_id: str) -> dict:
        """Return the bounded inputs behind both sealed roots for reviewers."""
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        effects = []
        for index in range(int(self.mission_effect_count[mission_id])):
            effects.append(self.get_effect_by_index(mission_id, index))
        evidence = []
        for index in range(int(self.mission_evidence_count[mission_id])):
            item = self.get_evidence_by_index(mission_id, index)
            item["authority"] = self.get_authority(item["authority_id"])
            evidence.append(item)
        return {
            "manifest_schema": MANIFEST_SCHEMA,
            "protocol": PROTOCOL,
            "revision": REVISION,
            "chain_id": int(gl.message.chain_id),
            "coordinator": gl.message.contract_address.as_hex,
            "mission_id": mission_id,
            "principal": self.mission_principal[mission_id].as_hex,
            "objective": self.mission_objective[mission_id],
            "policy_rule": POLICY_RULE,
            "policy_digest": self.mission_policy_digest[mission_id],
            "intent_digest": self.mission_intent_digest[mission_id],
            "state": self.mission_state[mission_id],
            "decision": self.mission_decision[mission_id],
            "reason_code": self.mission_reason_code[mission_id],
            "prepare_deadline": int(self.mission_prepare_deadline[mission_id]),
            "recovery_deadline": int(self.mission_recovery_deadline[mission_id]),
            "effect_count": int(self.mission_effect_count[mission_id]),
            "evidence_count": int(self.mission_evidence_count[mission_id]),
            "effect_root": self.mission_effect_root[mission_id],
            "evidence_root": self.mission_evidence_root[mission_id],
            "allocation_applied": self.mission_allocation_applied[mission_id],
            "effects": effects,
            "evidence": evidence,
        }

    @gl.public.view
    def is_supplier_authorized(self, mission_id: str, supplier: gl.Address) -> bool:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return self.supplier_authorized.get(mission_id + ":" + supplier.as_hex, False)
