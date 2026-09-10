# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""COMMIT deterministic mission registry.

This revision is deliberately non-payable and contains semantic evaluation but
no custody or settlement path. Custody is added only after the live
finality/payment canaries close their verification gates.
"""

from datetime import datetime, timezone
import json

import genlayer as gl
from genlayer.types import Keccak256


PROTOCOL = "commit"
REVISION = "0.3.0-evaluation"
STATE_PREPARING = "PREPARING"
STATE_SEALED = "SEALED"
STATE_ABORTED = "ABORTED"
MAX_TEXT = 512
MAX_EFFECTS = 32
MAX_EVIDENCE = 16


class CommitProtocol(gl.contract.Contract):
    owner: gl.Address
    mission_count: gl.u256
    mission_exists: gl.storage.TreeMap[str, bool]
    mission_principal: gl.storage.TreeMap[str, gl.Address]
    mission_state: gl.storage.TreeMap[str, str]
    mission_objective: gl.storage.TreeMap[str, str]
    mission_policy_digest: gl.storage.TreeMap[str, str]
    mission_intent_digest: gl.storage.TreeMap[str, str]
    mission_effect_root: gl.storage.TreeMap[str, str]
    mission_evidence_root: gl.storage.TreeMap[str, str]
    mission_budget: gl.storage.TreeMap[str, gl.u256]
    mission_prepared_value: gl.storage.TreeMap[str, gl.u256]
    mission_refund_beneficiary: gl.storage.TreeMap[str, gl.Address]
    mission_evidence_count: gl.storage.TreeMap[str, gl.u256]
    mission_decision: gl.storage.TreeMap[str, str]
    mission_reason_code: gl.storage.TreeMap[str, str]
    mission_evaluation_count: gl.storage.TreeMap[str, gl.u256]
    mission_prepare_deadline: gl.storage.TreeMap[str, gl.u256]
    mission_recovery_deadline: gl.storage.TreeMap[str, gl.u256]
    mission_version: gl.storage.TreeMap[str, gl.u256]
    mission_effect_count: gl.storage.TreeMap[str, gl.u256]
    effect_exists: gl.storage.TreeMap[str, bool]
    effect_mission: gl.storage.TreeMap[str, str]
    effect_supplier: gl.storage.TreeMap[str, gl.Address]
    effect_id: gl.storage.TreeMap[str, str]
    effect_digest: gl.storage.TreeMap[str, str]
    effect_beneficiary: gl.storage.TreeMap[str, gl.Address]
    effect_value: gl.storage.TreeMap[str, gl.u256]
    effect_expiry: gl.storage.TreeMap[str, gl.u256]
    mission_effect_key: gl.storage.TreeMap[str, str]
    authority_exists: gl.storage.TreeMap[str, bool]
    authority_host: gl.storage.TreeMap[str, str]
    authority_path_prefix: gl.storage.TreeMap[str, str]
    evidence_exists: gl.storage.TreeMap[str, bool]
    evidence_mission: gl.storage.TreeMap[str, str]
    evidence_id: gl.storage.TreeMap[str, str]
    evidence_authority: gl.storage.TreeMap[str, str]
    evidence_url: gl.storage.TreeMap[str, str]
    evidence_record_hash: gl.storage.TreeMap[str, str]
    evidence_subject: gl.storage.TreeMap[str, str]
    evidence_expires_at: gl.storage.TreeMap[str, gl.u256]
    mission_evidence_key: gl.storage.TreeMap[str, str]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.mission_count = gl.u256(0)
        # v0.6 storage collections are allocated by the contract runtime.

    def _require_digest(self, value: str, label: str) -> None:
        if len(value) != 64:
            raise gl.vm.UserError(f"{label} must be 32-byte lowercase hex")
        for char in value:
            if char not in "0123456789abcdef":
                raise gl.vm.UserError(f"{label} must be 32-byte lowercase hex")

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

    def _require_path_prefix(self, value: str) -> None:
        self._require_ascii_text(value, "authority path prefix", MAX_TEXT)
        if not value.startswith("/") or "//" in value or any(
            marker in value for marker in ("?", "#", "%", "\\")
        ):
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
        segments = remainder.split("/")
        if any(segment in ("", ".", "..") for segment in segments[1:]):
            return False
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
            "1",
            mission_id,
            objective,
            policy_digest,
            str(budget),
            refund_beneficiary.as_hex,
            str(prepare_deadline),
            str(recovery_deadline),
        )
        payload = "commit-intent-v1" + "".join(self._frame(field) for field in fields)
        return Keccak256(payload.encode("utf-8")).hexdigest()

    @gl.public.write
    def register_authority(self, authority_id: str, host: str, path_prefix: str) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("owner required")
        self._require_identifier(authority_id, "authority id", 64)
        if self.authority_exists.get(authority_id, False):
            raise gl.vm.UserError("authority already exists")
        self._require_authority_host(host)
        self._require_path_prefix(path_prefix)
        self.authority_exists[authority_id] = True
        self.authority_host[authority_id] = host
        self.authority_path_prefix[authority_id] = path_prefix

    @gl.public.write
    def register_evidence(
        self,
        mission_id: str,
        evidence_id: str,
        authority_id: str,
        url: str,
        record_hash: str,
        subject: str,
        expires_at: int,
    ) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
        self._require_identifier(evidence_id, "evidence id", MAX_TEXT)
        evidence_key = mission_id + ":" + evidence_id
        if self.evidence_exists.get(evidence_key, False):
            raise gl.vm.UserError("evidence already exists")
        evidence_index = int(self.mission_evidence_count[mission_id])
        if evidence_index >= MAX_EVIDENCE:
            raise gl.vm.UserError("evidence limit exceeded")
        self._require_authority(authority_id)
        if not self._url_matches_authority(
            url,
            self.authority_host[authority_id],
            self.authority_path_prefix[authority_id],
        ):
            raise gl.vm.UserError("evidence URL is outside authority")
        self._require_digest(record_hash, "record hash")
        self._require_ascii_text(subject, "evidence subject")
        if subject != mission_id:
            raise gl.vm.UserError("evidence subject mismatch")
        if expires_at < int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("invalid evidence expiry")

        self.evidence_exists[evidence_key] = True
        self.evidence_mission[evidence_key] = mission_id
        self.evidence_id[evidence_key] = evidence_id
        self.evidence_authority[evidence_key] = authority_id
        self.evidence_url[evidence_key] = url
        self.evidence_record_hash[evidence_key] = record_hash
        self.evidence_subject[evidence_key] = subject
        self.evidence_expires_at[evidence_key] = gl.u256(expires_at)
        self.mission_evidence_key[mission_id + ":" + str(evidence_index)] = evidence_key
        self.mission_evidence_count[mission_id] = gl.u256(evidence_index + 1)

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
        if self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission already exists")
        self._require_nonzero_address(refund_beneficiary, "refund beneficiary")
        if budget <= 0:
            raise gl.vm.UserError("mission budget must be positive")
        if prepare_deadline <= 0 or recovery_deadline <= prepare_deadline:
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
        self.mission_budget[mission_id] = gl.u256(budget)
        self.mission_prepared_value[mission_id] = gl.u256(0)
        self.mission_refund_beneficiary[mission_id] = refund_beneficiary
        self.mission_evidence_count[mission_id] = gl.u256(0)
        self.mission_decision[mission_id] = ""
        self.mission_reason_code[mission_id] = ""
        self.mission_evaluation_count[mission_id] = gl.u256(0)
        self.mission_prepare_deadline[mission_id] = gl.u256(prepare_deadline)
        self.mission_recovery_deadline[mission_id] = gl.u256(recovery_deadline)
        self.mission_version[mission_id] = gl.u256(1)
        self.mission_effect_count[mission_id] = gl.u256(0)
        self.mission_count = gl.u256(self.mission_count + 1)

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
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if int(datetime.now(timezone.utc).timestamp()) > int(self.mission_prepare_deadline[mission_id]):
            raise gl.vm.UserError("preparation deadline has passed")
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
        if value <= 0:
            raise gl.vm.UserError("effect value must be positive")
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
        self.effect_beneficiary[effect_key] = beneficiary
        self.effect_value[effect_key] = gl.u256(value)
        self.effect_expiry[effect_key] = gl.u256(expiry)
        self.mission_prepared_value[mission_id] = gl.u256(
            int(self.mission_prepared_value[mission_id]) + value
        )
        self.mission_effect_key[mission_id + ":" + str(effect_index)] = effect_key
        self.mission_effect_count[mission_id] = gl.u256(effect_index + 1)

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
        if not self._has_distinct_evidence_authorities(mission_id):
            raise gl.vm.UserError("evidence authorities must be distinct")
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
        self.mission_state[mission_id] = STATE_ABORTED

    @gl.public.write
    def evaluate_mission(self, mission_id: str) -> None:
        self._require_principal(mission_id)
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

        def leader_fn() -> dict:
            all_eligible = True
            for evidence_id, authority_id, url, expected_hash, expected_expiry in source_specs:
                response = gl.nondet.web.get(url)
                if response.status != 200:
                    raise gl.vm.UserError("evidence source unavailable")
                record = json.loads(response.body.decode("utf-8"))
                if not isinstance(record, dict):
                    raise gl.vm.UserError("evidence record must be an object")
                if record.get("schema") != "commit-evidence-v1":
                    raise gl.vm.UserError("unsupported evidence schema")
                if record.get("evidence_id") != evidence_id:
                    raise gl.vm.UserError("evidence id mismatch")
                if record.get("authority_id") != authority_id:
                    raise gl.vm.UserError("evidence authority mismatch")
                if record.get("url") != url:
                    raise gl.vm.UserError("evidence URL mismatch")
                if record.get("subject") != mission_id_snapshot:
                    raise gl.vm.UserError("evidence subject mismatch")
                if record.get("expires_at") != int(expected_expiry):
                    raise gl.vm.UserError("evidence expiry mismatch")
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    raise gl.vm.UserError("evidence payload must be an object")
                if set(payload.keys()) != {"eligible", "reason_code"}:
                    raise gl.vm.UserError("unsupported evidence payload")
                if type(payload.get("eligible")) is not bool:
                    raise gl.vm.UserError("evidence eligibility missing")
                if type(payload.get("reason_code")) is not str or not payload["reason_code"]:
                    raise gl.vm.UserError("evidence reason missing")
                canonical_payload = json.dumps(
                    payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                )
                computed_hash = Keccak256(canonical_payload.encode("utf-8")).hexdigest()
                if computed_hash != expected_hash:
                    raise gl.vm.UserError("evidence payload hash mismatch")
                if not payload["eligible"]:
                    all_eligible = False
            return {
                "decision": "COMMIT" if all_eligible else "ABORT",
                "reason_code": "all_sources_eligible" if all_eligible else "source_ineligible",
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
            )

        result = gl.vm.run_nondet(leader_fn, validator_fn)
        if result["decision"] not in ("COMMIT", "ABORT"):
            raise gl.vm.UserError("invalid consensus decision")
        self.mission_decision[mission_id] = result["decision"]
        self.mission_reason_code[mission_id] = result["reason_code"]
        self.mission_evaluation_count[mission_id] = gl.u256(
            int(self.mission_evaluation_count[mission_id]) + 1
        )

    @gl.public.write
    def expire_mission(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if self.mission_state[mission_id] not in (STATE_PREPARING, STATE_SEALED):
            raise gl.vm.UserError("mission is already terminal")
        now = int(datetime.now(timezone.utc).timestamp())
        if now < int(self.mission_recovery_deadline[mission_id]):
            raise gl.vm.UserError("recovery deadline has not passed")
        self.mission_state[mission_id] = STATE_ABORTED

    @gl.public.view
    def protocol_info(self) -> dict:
        return {
            "protocol": PROTOCOL,
            "revision": REVISION,
            "custody_enabled": False,
            "semantic_evaluation_enabled": True,
            "mission_count": int(self.mission_count),
        }

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

    def _has_distinct_evidence_authorities(self, mission_id: str) -> bool:
        first = self.evidence_authority[
            self.mission_evidence_key[mission_id + ":0"]
        ]
        count = int(self.mission_evidence_count[mission_id])
        for index in range(1, count):
            key = self.mission_evidence_key[mission_id + ":" + str(index)]
            if self.evidence_authority[key] != first:
                return True
        return False

    def _frame(self, value: str) -> str:
        return str(len(value)) + ":" + value

    def _effect_leaf(self, effect_key: str) -> str:
        fields = (
            self.effect_id[effect_key],
            self.effect_digest[effect_key],
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
            self.evidence_url[evidence_key],
            self.evidence_record_hash[evidence_key],
            self.evidence_subject[evidence_key],
            str(int(self.evidence_expires_at[evidence_key])),
        )
        payload = "commit-evidence-leaf-v1" + "".join(
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
        payload = "commit-evidence-root-v1" + self._frame(str(count))
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
            "budget": int(self.mission_budget[mission_id]),
            "prepared_value": int(self.mission_prepared_value[mission_id]),
            "refund_beneficiary": self.mission_refund_beneficiary[mission_id].as_hex,
            "effect_count": int(self.mission_effect_count[mission_id]),
            "evidence_count": int(self.mission_evidence_count[mission_id]),
            "decision": self.mission_decision[mission_id],
            "reason_code": self.mission_reason_code[mission_id],
            "evaluation_count": int(self.mission_evaluation_count[mission_id]),
            "prepare_deadline": int(self.mission_prepare_deadline[mission_id]),
            "recovery_deadline": int(self.mission_recovery_deadline[mission_id]),
        }

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
            "beneficiary": self.effect_beneficiary[effect_key].as_hex,
            "value": int(self.effect_value[effect_key]),
            "expiry": int(self.effect_expiry[effect_key]),
        }

    @gl.public.view
    def get_authority(self, authority_id: str) -> dict:
        self._require_authority(authority_id)
        return {
            "authority_id": authority_id,
            "host": self.authority_host[authority_id],
            "path_prefix": self.authority_path_prefix[authority_id],
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
            "url": self.evidence_url[evidence_key],
            "record_hash": self.evidence_record_hash[evidence_key],
            "subject": self.evidence_subject[evidence_key],
            "expires_at": int(self.evidence_expires_at[evidence_key]),
        }
