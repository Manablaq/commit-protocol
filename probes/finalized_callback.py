# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""Zero-value runtime probe. This is not the COMMIT custody contract."""

import genlayer as gl


class FinalizedCallbackProbe(gl.contract.Contract):
    owner: gl.Address
    pending: str
    applied: bool
    applications: gl.u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.pending = ""
        self.applied = False
        self.applications = gl.u256(0)

    @gl.public.write
    def request(self, identifier: str) -> None:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("owner required")
        if self.pending or not identifier or len(identifier) > 64:
            raise gl.vm.UserError("invalid or duplicate request")
        self.pending = identifier
        gl.contract.get_at(gl.message.contract_address).emit(on="finalized").apply(identifier)

    @gl.public.write
    def apply(self, identifier: str) -> None:
        if gl.message.sender_address != gl.message.contract_address:
            raise gl.vm.UserError("self message required")
        if not self.pending or identifier != self.pending:
            raise gl.vm.UserError("request mismatch")
        if self.applied:
            return
        self.applied = True
        self.applications = gl.u256(self.applications + 1)

    @gl.public.view
    def state(self) -> dict:
        return {"pending": self.pending, "applied": self.applied,
                "applications": int(self.applications)}
