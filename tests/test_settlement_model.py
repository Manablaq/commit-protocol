import unittest
from dataclasses import replace

from spec_model.settlement import Mission, Rejected, explore, step


def sequence(*events):
    state = Mission()
    for event in events:
        state = step(state, event)
        state.check()
    return state


class SettlementModelTests(unittest.TestCase):
    def test_complete_finite_state_space(self):
        report = explore()
        self.assertEqual(report["phases"], ["abort", "commit", "pending", "sealed"])
        self.assertTrue(report["complete_commit_payment"])
        self.assertTrue(report["complete_abort_refund"])
        self.assertTrue(report["unresolved_payment"])

    def test_provisional_decision_cannot_allocate(self):
        state = sequence("propose_commit")
        with self.assertRaises(Rejected):
            step(state, "callback")

    def test_recovery_wins_against_late_callback(self):
        state = sequence("propose_commit", "parent_finalizes", "deadline", "recover")
        self.assertEqual(step(state, "callback"), state)
        self.assertEqual(state.refund, 3)

    def test_commit_wins_against_recovery(self):
        state = sequence("propose_commit", "parent_finalizes", "callback", "deadline")
        with self.assertRaises(Rejected):
            step(state, "recover")

    def test_appeal_changes_result_without_payment(self):
        state = sequence("propose_commit", "appeal_flip", "parent_finalizes", "callback")
        self.assertEqual(state.phase, "abort")
        self.assertEqual(state.refund, 3)

    def test_unknown_transfer_neither_refunds_nor_retries(self):
        state = sequence("propose_commit", "parent_finalizes", "callback", "claim:0")
        self.assertEqual(step(state, "unknown:0"), state)
        with self.assertRaises(Rejected):
            step(state, "claim:0")

    def test_proven_restoration_preserves_beneficiary(self):
        state = sequence("propose_commit", "parent_finalizes", "callback", "claim:0",
                         "restored_failure:0", "claim:0", "payment_success:0")
        self.assertEqual(state.delivered, (1, 0, 0))
        with self.assertRaises(Rejected):
            step(state, "payment_success:0")

    def test_invariant_detects_premature_commit_mutation(self):
        faulty = replace(Mission(), phase="commit", locked=0, supplier_a=1,
                         supplier_b=1, refund=1, decision="commit", allocations=1)
        with self.assertRaises(AssertionError):
            faulty.check()

    def test_invariant_detects_restoring_already_delivered_money(self):
        state = sequence("propose_commit", "parent_finalizes", "callback", "claim:0",
                         "payment_success:0")
        with self.assertRaises(AssertionError):
            replace(state, supplier_a=1).check()

    def test_invariant_detects_abort_supplier_payout(self):
        state = sequence("deadline", "recover")
        with self.assertRaises(AssertionError):
            replace(state, refund=2, supplier_a=1).check()


if __name__ == "__main__":
    unittest.main()
