"""Finite model of allocation/recovery races for one funded two-effect mission.

Events such as finalization and transfer outcomes are supplied by the model
checker. They are assumptions about a future adapter, not implemented proofs.
"""

from dataclasses import dataclass, replace


class Rejected(ValueError):
    pass


@dataclass(frozen=True)
class Mission:
    phase: str = "sealed"
    locked: int = 3
    supplier_a: int = 0
    supplier_b: int = 0
    refund: int = 0
    # One pending transfer per beneficiary in this finite abstraction.
    dispatched: tuple[int, int, int] = (0, 0, 0)
    delivered: tuple[int, int, int] = (0, 0, 0)
    decision: str = ""
    finalized_parent: bool = False
    expired: bool = False
    allocations: int = 0

    def check(self):
        values = (self.locked, self.supplier_a, self.supplier_b, self.refund,
                  *self.dispatched, *self.delivered)
        assert all(type(v) is int and v >= 0 for v in values), self
        assert sum(values) == 3, self
        assert self.allocations in (0, 1), self
        if self.phase in ("sealed", "pending"):
            assert self.locked == 3 and self.allocations == 0, self
        elif self.phase == "commit":
            assert self.finalized_parent and self.decision == "commit", self
            assert self.locked == 0 and self.allocations == 1, self
            assert self.supplier_a + self.dispatched[0] + self.delivered[0] == 1, self
            assert self.supplier_b + self.dispatched[1] + self.delivered[1] == 1, self
            assert self.refund + self.dispatched[2] + self.delivered[2] == 1, self
        elif self.phase == "abort":
            assert self.locked == 0 and self.allocations == 1, self
            assert self.supplier_a == self.supplier_b == 0, self
            assert self.dispatched[:2] == self.delivered[:2] == (0, 0), self
            assert self.refund + self.dispatched[2] + self.delivered[2] == 3, self
        else:
            raise AssertionError(self.phase)


def step(s: Mission, event: str) -> Mission:
    if event == "deadline":
        return replace(s, expired=True)
    if event in ("propose_commit", "propose_abort"):
        if s.phase != "sealed" or s.expired:
            raise Rejected("not eligible")
        return replace(s, phase="pending", decision=event.removeprefix("propose_"))
    if event == "appeal_flip":
        if s.phase != "pending" or s.finalized_parent:
            raise Rejected("not appealable")
        return replace(s, decision="abort" if s.decision == "commit" else "commit")
    if event == "parent_finalizes":
        if s.phase != "pending":
            raise Rejected("no pending decision")
        return replace(s, finalized_parent=True)
    if event in ("callback", "forged_callback"):
        if event == "forged_callback":
            raise Rejected("unauthenticated sender")
        if s.phase in ("commit", "abort"):
            return s  # Duplicate or late callback cannot reopen allocation.
        if s.phase != "pending" or not s.finalized_parent:
            raise Rejected("parent not finalized")
        if s.decision == "commit":
            return replace(s, phase="commit", locked=0, supplier_a=1,
                           supplier_b=1, refund=1, allocations=1)
        return replace(s, phase="abort", locked=0, refund=3, allocations=1)
    if event == "recover":
        if not s.expired or s.phase not in ("sealed", "pending"):
            raise Rejected("not recoverable")
        return replace(s, phase="abort", locked=0, refund=3, allocations=1)
    kind, _, index = event.partition(":")
    if kind not in ("claim", "payment_success", "restored_failure", "unknown"):
        raise Rejected("unknown event")
    if index not in ("0", "1", "2"):
        raise Rejected("bad beneficiary")
    i = int(index)
    if s.phase not in ("commit", "abort"):
        raise Rejected("unallocated")
    fields = ("supplier_a", "supplier_b", "refund")
    pending = list(s.dispatched)
    delivered = list(s.delivered)
    if kind == "claim":
        amount = getattr(s, fields[i])
        if amount == 0 or pending[i]:
            raise Rejected("no available entitlement")
        pending[i] = amount
        return replace(s, **{fields[i]: 0}, dispatched=tuple(pending))
    if not pending[i]:
        raise Rejected("no matching outstanding transfer")
    if kind == "unknown":
        return s
    amount = pending[i]
    pending[i] = 0
    if kind == "payment_success":
        delivered[i] += amount
        return replace(s, dispatched=tuple(pending), delivered=tuple(delivered))
    return replace(s, **{fields[i]: getattr(s, fields[i]) + amount},
                   dispatched=tuple(pending))


EVENTS = (
    "deadline", "propose_commit", "propose_abort", "appeal_flip",
    "parent_finalizes", "callback", "forged_callback", "recover",
    *(f"{kind}:{i}" for kind in
      ("claim", "payment_success", "restored_failure", "unknown") for i in range(3)),
)


def explore():
    """Enumerate the complete reachable state space of this finite abstraction."""
    initial = Mission()
    seen = {initial}
    frontier = [initial]
    edges = rejected = 0
    while frontier:
        state = frontier.pop()
        state.check()
        for event in EVENTS:
            try:
                following = step(state, event)
            except Rejected:
                rejected += 1
                continue
            following.check()
            edges += 1
            if following not in seen:
                seen.add(following)
                frontier.append(following)
    return {"states": len(seen), "valid_edges": edges, "rejected_edges": rejected,
            "phases": sorted({s.phase for s in seen}),
            "complete_commit_payment": any(s.delivered == (1, 1, 1) for s in seen),
            "complete_abort_refund": any(s.delivered == (0, 0, 3) for s in seen),
            "unresolved_payment": any(any(s.dispatched) for s in seen)}


if __name__ == "__main__":
    import json
    print(json.dumps(explore(), indent=2))
