import copy
import unittest

from axm_neural_network.host_bridge import (
    AXM_ROOT_CONTRACT_REF,
    BridgeContract,
    HostBrainBridge,
    HostEvent,
    sha256_json,
)
from neural.axm_brain import AXM_ROOT_CONTRACT, BoundBrain, BrainIOContract

BRAIN_IO = {
    "schema": "axm-brain-io/v0.1",
    "name": "portable-host-proof/v0.1",
    "inputs": [{"name": "signal", "minimum": 0.0, "maximum": 1.0, "default": 0.0}],
    "outputs": ["reuse", "explore"],
}

def make_bridge():
    contract = BridgeContract(name="portable-host-proof/v2", brain_io=copy.deepcopy(BRAIN_IO))
    bound = BrainIOContract.from_dict(copy.deepcopy(BRAIN_IO)).new_brain(
        hidden_size=6, seed=29, replay_capacity=32, sleep_replay_passes=1
    )
    return HostBrainBridge(bound, contract)

def make_event(contract, event_id, target=None):
    return HostEvent(
        contract_sha256=contract.fingerprint,
        event_id=event_id,
        observations={"signal": 1.0},
        target=target,
        directions=("USE", "LEARN"),
    )

class HostBridgeV2Tests(unittest.TestCase):
    def test_root_reference_matches_current_core(self):
        self.assertEqual(
            AXM_ROOT_CONTRACT_REF["contract_sha256"],
            AXM_ROOT_CONTRACT.fingerprint,
        )

    def test_behavior_change_retains_after_host_owned_restore(self):
        bridge = make_bridge()
        before = bridge.experience(make_event(bridge.contract, "before")).values
        target = {"reuse": 1.0, "explore": -1.0}
        for index in range(120):
            bridge.experience(make_event(bridge.contract, f"teach-{index}", target))
        bridge.bound_brain.brain.sleep()
        bridge.bound_brain.brain.wake()
        after = bridge.experience(make_event(bridge.contract, "after")).values
        self.assertGreater(after["reuse"], before["reuse"])
        self.assertLess(after["explore"], before["explore"])

        host_snapshot = bridge.bound_brain.to_snapshot()
        receipt = bridge.export_state_reference("checkpoint-001")
        restored = BoundBrain.from_snapshot(copy.deepcopy(host_snapshot))
        restored_bridge = HostBrainBridge.restore_from_host_state(
            receipt,
            restored_bound_brain=restored,
            expected_contract=bridge.contract,
        )
        self.assertEqual(
            bridge.experience(make_event(bridge.contract, "next")).to_dict(),
            restored_bridge.experience(make_event(bridge.contract, "next")).to_dict(),
        )

    def test_state_reference_contains_no_neural_state(self):
        bridge = make_bridge()
        receipt = bridge.export_state_reference("checkpoint-002")
        body = receipt["body"]
        self.assertFalse(body["contains_neural_state"])
        self.assertTrue(body["host_owned_persistence"])
        self.assertFalse(body["execution_authorized"])
        serialized = repr(receipt)
        for forbidden in ("bound_brain", "w_in", "w_rec", "w_out", "replay"):
            self.assertNotIn(forbidden, serialized)

    def test_tamper_and_semantic_rehash_fail_closed(self):
        bridge = make_bridge()
        receipt = bridge.export_state_reference("checkpoint-003")
        tampered = copy.deepcopy(receipt)
        tampered["body"]["state_ref"] = "different"
        with self.assertRaises(ValueError):
            HostBrainBridge.restore_from_host_state(
                tampered,
                restored_bound_brain=bridge.bound_brain,
                expected_contract=bridge.contract,
            )

        semantic = copy.deepcopy(receipt)
        semantic["body"]["contains_neural_state"] = True
        semantic["sha256"] = sha256_json(semantic["body"])
        with self.assertRaises(ValueError):
            HostBrainBridge.restore_from_host_state(
                semantic,
                restored_bound_brain=bridge.bound_brain,
                expected_contract=bridge.contract,
            )

if __name__ == "__main__":
    unittest.main()
