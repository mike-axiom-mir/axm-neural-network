import copy
import unittest

from axm_bridge import (
    HostBrainBridge,
    HostEvent,
    UC_BRAIN_IO,
    build_uc_bridge_contract,
    build_uc_event,
)

try:
    from neural.axm_brain import BoundBrain, BrainIOContract
except ImportError as exc:
    raise RuntimeError(
        "Pinned axm-uc-neural donor must be on PYTHONPATH for integration tests"
    ) from exc


class UCDonorIntegrationTests(unittest.TestCase):
    def make_bridge(self):
        donor_io = BrainIOContract.from_dict(copy.deepcopy(UC_BRAIN_IO))
        bound = donor_io.new_brain(
            hidden_size=6,
            seed=23,
            replay_capacity=32,
            sleep_replay_passes=1,
        )
        return HostBrainBridge(bound, build_uc_bridge_contract())

    def test_uc_event_changes_retained_host_readable_response(self):
        bridge = self.make_bridge()
        contract = bridge.contract
        before = bridge.experience(
            build_uc_event(
                contract=contract,
                event_id="probe-before",
                route_class="COMPATIBLE_AND_SUFFICIENT",
                artifact_verified=True,
                candidate_reused=True,
            )
        ).values

        target = {
            "reuse_preference": 0.9,
            "explore_preference": -0.9,
        }
        for index in range(80):
            bridge.experience(
                build_uc_event(
                    contract=contract,
                    event_id=f"teach-{index}",
                    route_class="COMPATIBLE_AND_SUFFICIENT",
                    artifact_verified=True,
                    candidate_reused=True,
                    target=target,
                    reward=1.0,
                )
            )

        bridge.bound_brain.brain.sleep()
        bridge.bound_brain.brain.wake()

        after = bridge.experience(
            build_uc_event(
                contract=contract,
                event_id="probe-after",
                route_class="COMPATIBLE_AND_SUFFICIENT",
                artifact_verified=True,
                candidate_reused=True,
            )
        ).values

        self.assertGreater(after["reuse_preference"], before["reuse_preference"])
        self.assertLess(after["explore_preference"], before["explore_preference"])

    def test_restart_restores_equivalent_next_host_output(self):
        bridge = self.make_bridge()
        contract = bridge.contract
        for index in range(20):
            bridge.experience(
                build_uc_event(
                    contract=contract,
                    event_id=f"experience-{index}",
                    route_class="COMPATIBLE_AND_SUFFICIENT",
                    artifact_verified=True,
                    candidate_reused=(index % 2 == 0),
                    target={
                        "reuse_preference": 0.7,
                        "explore_preference": -0.4,
                    },
                )
            )

        checkpoint = bridge.export_checkpoint()
        restored_a = HostBrainBridge.restore(
            checkpoint,
            bound_brain_type=BoundBrain,
            expected_contract=contract,
        )
        restored_b = HostBrainBridge.restore(
            checkpoint,
            bound_brain_type=BoundBrain,
            expected_contract=contract,
        )
        event = build_uc_event(
            contract=contract,
            event_id="post-restart",
            route_class="COMPATIBLE_BUT_INSUFFICIENT",
            artifact_verified=False,
            candidate_reused=False,
        )
        self.assertEqual(
            restored_a.experience(event).to_dict(),
            restored_b.experience(event).to_dict(),
        )

    def test_contract_mismatch_fails_before_experience_is_counted(self):
        bridge = self.make_bridge()
        before = bridge.bound_brain.brain.host_experience_count
        bad = HostEvent(
            contract_sha256="f" * 64,
            event_id="wrong-contract",
            observations={"route_ready": 1.0},
        )
        with self.assertRaises(ValueError):
            bridge.experience(bad)
        self.assertEqual(before, bridge.bound_brain.brain.host_experience_count)

    def test_checkpoint_tamper_is_rejected(self):
        bridge = self.make_bridge()
        checkpoint = bridge.export_checkpoint()
        checkpoint["body"]["contract"]["name"] = "silent-rewrite"
        with self.assertRaises(ValueError):
            HostBrainBridge.restore(
                checkpoint,
                bound_brain_type=BoundBrain,
            )

    def test_output_is_named_and_advisory(self):
        bridge = self.make_bridge()
        proposal = bridge.experience(
            build_uc_event(
                contract=bridge.contract,
                event_id="proposal",
                route_class="UNKNOWN_HOLD",
                artifact_verified=False,
                candidate_reused=False,
            )
        )
        self.assertEqual(
            set(proposal.values),
            {"reuse_preference", "explore_preference"},
        )
        self.assertTrue(proposal.advisory_only)


if __name__ == "__main__":
    unittest.main()
