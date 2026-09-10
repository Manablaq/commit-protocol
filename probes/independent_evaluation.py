# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""Minimal GenLayer consensus probe for independent evidence evaluation.

This is not the production COMMIT contract. It isolates the v0.6 API and
validator rule before the result is connected to any settlement state. Both
URLs are supplied by the caller only for the probe; production code must add
registered-authority and provenance enforcement first.
"""

import json

import genlayer as gl


class IndependentEvaluationProbe(gl.contract.Contract):
    last_decision: str
    last_reason_code: str
    evaluation_count: gl.u256

    def __init__(self):
        self.last_decision = "UNSET"
        self.last_reason_code = "UNSET"
        self.evaluation_count = gl.u256(0)

    def _read_record(self, url: str) -> dict:
        response = gl.nondet.web.get(url)
        if response.status != 200:
            raise gl.vm.UserError("evidence source unavailable")
        record = json.loads(response.body.decode("utf-8"))
        if not isinstance(record, dict):
            raise gl.vm.UserError("evidence record must be an object")
        if record.get("schema") != "commit-evidence-v1":
            raise gl.vm.UserError("unsupported evidence schema")
        if record.get("eligible") not in (True, False):
            raise gl.vm.UserError("evidence eligibility missing")
        reason_code = record.get("reason_code")
        if not isinstance(reason_code, str) or not reason_code:
            raise gl.vm.UserError("evidence reason missing")
        return record

    @gl.public.write
    def evaluate(self, source_a_url: str, source_b_url: str) -> None:
        if not source_a_url or not source_b_url or source_a_url == source_b_url:
            raise gl.vm.UserError("two distinct evidence URLs required")

        def leader_fn() -> dict:
            record_a = self._read_record(source_a_url)
            record_b = self._read_record(source_b_url)
            eligible = record_a["eligible"] and record_b["eligible"]
            return {
                "decision": "COMMIT" if eligible else "ABORT",
                "reason_code": "all_sources_eligible" if eligible else "source_ineligible",
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            validator_data = leader_fn()
            leader_data = leader_result.calldata
            if not isinstance(leader_data, dict):
                return False
            return (
                leader_data.get("decision") == validator_data["decision"]
                and leader_data.get("reason_code") == validator_data["reason_code"]
            )

        # The pinned v0.6 runner exposes the custom leader/validator primitive
        # as run_nondet. The newer documentation also refers to an
        # experimental run_nondet_unsafe name; do not call an API absent from
        # the selected runtime.
        result = gl.vm.run_nondet(leader_fn, validator_fn)
        if result["decision"] not in ("COMMIT", "ABORT"):
            raise gl.vm.UserError("invalid consensus decision")
        self.last_decision = result["decision"]
        self.last_reason_code = result["reason_code"]
        self.evaluation_count = gl.u256(self.evaluation_count + 1)

    @gl.public.view
    def state(self) -> dict:
        return {
            "last_decision": self.last_decision,
            "last_reason_code": self.last_reason_code,
            "evaluation_count": int(self.evaluation_count),
        }
