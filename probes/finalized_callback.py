# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Zero-value runtime probe. This is not the COMMIT custody contract."""

from genlayer import *


class FinalizedCallbackProbe(gl.Contract):
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
        gl.get_contract_at(gl.message.contract_address).emit(on="finalized").apply(identifier)

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
