# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""COMMIT deterministic mission registry skeleton.

This revision is deliberately non-payable and contains no semantic evaluation or
settlement path. Custody is added only after the live finality/payment canaries
close their verification gates.
"""

from datetime import datetime, timezone

import genlayer as gl
from genlayer.types import Keccak256


PROTOCOL = "commit"
REVISION = "0.1.0-skeleton"
STATE_PREPARING = "PREPARING"
STATE_SEALED = "SEALED"
STATE_ABORTED = "ABORTED"
MAX_TEXT = 512


class CommitProtocol(gl.contract.Contract):
    owner: gl.Address
    mission_count: gl.u256
    mission_exists: gl.storage.TreeMap[str, bool]
    mission_principal: gl.storage.TreeMap[str, gl.Address]
    mission_state: gl.storage.TreeMap[str, str]
    mission_intent_digest: gl.storage.TreeMap[str, str]
    mission_effect_root: gl.storage.TreeMap[str, str]
    mission_evidence_root: gl.storage.TreeMap[str, str]
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

    def _require_mission_id(self, value: str) -> None:
        if not value or len(value) > MAX_TEXT or ":" in value:
            raise gl.vm.UserError("invalid mission id")

    @gl.public.write
    def create_mission(
        self,
        mission_id: str,
        intent_digest: str,
        prepare_deadline: int,
        recovery_deadline: int,
    ) -> None:
        self._require_mission_id(mission_id)
        self._require_digest(intent_digest, "intent digest")
        if self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission already exists")
        if prepare_deadline <= 0 or recovery_deadline <= prepare_deadline:
            raise gl.vm.UserError("invalid deadline order")

        self.mission_exists[mission_id] = True
        self.mission_principal[mission_id] = gl.message.sender_address
        self.mission_state[mission_id] = STATE_PREPARING
        self.mission_intent_digest[mission_id] = intent_digest
        self.mission_effect_root[mission_id] = ""
        self.mission_evidence_root[mission_id] = ""
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
        if not effect_id or len(effect_id) > MAX_TEXT or ":" in effect_id:
            raise gl.vm.UserError("invalid effect id")
        effect_key = mission_id + ":" + effect_id
        if self.effect_exists.get(effect_key, False):
            raise gl.vm.UserError("effect already exists")
        self._require_digest(effect_digest, "effect digest")
        if value <= 0:
            raise gl.vm.UserError("effect value must be positive")
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
        effect_index = int(self.mission_effect_count[mission_id])
        self.mission_effect_key[mission_id + ":" + str(effect_index)] = effect_key
        self.mission_effect_count[mission_id] = gl.u256(effect_index + 1)

    @gl.public.write
    def seal_mission(self, mission_id: str, effect_root: str, evidence_root: str) -> None:
        self._require_principal(mission_id)
        if self.mission_state[mission_id] != STATE_PREPARING:
            raise gl.vm.UserError("mission is not preparing")
        if self.mission_effect_count[mission_id] <= 0:
            raise gl.vm.UserError("mission has no prepared effects")
        self._require_digest(effect_root, "effect root")
        self._require_digest(evidence_root, "evidence root")
        if effect_root != self.derive_effect_root(mission_id):
            raise gl.vm.UserError("effect root does not match prepared effects")
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
            "semantic_evaluation_enabled": False,
            "mission_count": int(self.mission_count),
        }

    def _require_principal(self, mission_id: str) -> None:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        if gl.message.sender_address != self.mission_principal[mission_id]:
            raise gl.vm.UserError("principal required")

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
    def get_mission(self, mission_id: str) -> dict:
        if not self.mission_exists.get(mission_id, False):
            raise gl.vm.UserError("mission not found")
        return {
            "mission_id": mission_id,
            "principal": self.mission_principal[mission_id].as_hex,
            "state": self.mission_state[mission_id],
            "version": int(self.mission_version[mission_id]),
            "intent_digest": self.mission_intent_digest[mission_id],
            "effect_root": self.mission_effect_root[mission_id],
            "evidence_root": self.mission_evidence_root[mission_id],
            "effect_count": int(self.mission_effect_count[mission_id]),
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
