import copy
import unittest

from axm_neural_network.host_bridge import (
    BridgeContract,
    HostBrainBridge,
    HostEvent,
    sha256_json,
)

BRAIN_IO = {
    "schema": "axm-brain-io/v0.1",
    "name": "bridge-unit-proof/v0.1",
    "inputs": [{"name": "signal", "minimum": 0.0, "maximum": 1.0, "default": 0.0}],
    "outputs": ["reuse", "explore"],
}

class FakeIO:
    def __init__(self):
        self.fingerprint = sha256_json(BRAIN_IO)
    def to_dict(self):
        return copy.deepcopy(BRAIN_IO)

class FakeBrain:
    def __init__(self, value=0.0):
        self.contract = FakeIO()
        self.value = float(value)
        self.count = 0
    def experience(self, observations, **kwargs):
        self.count += 1
        target = kwargs.get("target")
        if target is not None:
            self.value += 0.05 * float(target[0])
        return [self.value, -self.value]
    def output_state(self, raw):
        return {"reuse": float(raw[0]), "explore": float(raw[1])}
    def to_snapshot(self):
        return {"schema": "test-brain/v1", "value": self.value, "count": self.count}

def make_bridge(value=0.0):
    contract = BridgeContract(name="bridge-unit-proof/v2", brain_io=copy.deepcopy(BRAIN_IO))
    return HostBrainBridge(FakeBrain(value), contract)

class HostBridgeV2StateRefTests(unittest.TestCase):
    def test_state_reference_contains_only_state_identity(self):
        bridge = make_bridge()
        receipt = bridge.export_state_reference("checkpoint-001")
        body = receipt["body"]
        self.assertFalse(body["contains_neural_state"])
        self.assertTrue(body["host_owned_persistence"])
        self.assertIn("brain_state_sha256", body)
        self.assertNotIn("bound_brain", repr(receipt))

    def test_restore_requires_matching_host_state(self):
        bridge = make_bridge(0.25)
        receipt = bridge.export_state_reference("checkpoint-002")
        restored = HostBrainBridge.restore_from_host_state(
            receipt,
            restored_bound_brain=FakeBrain(0.25),
            expected_contract=bridge.contract,
        )
        self.assertEqual(restored.bound_brain.value, 0.25)
        with self.assertRaises(ValueError):
            HostBrainBridge.restore_from_host_state(
                receipt,
                restored_bound_brain=FakeBrain(0.75),
                expected_contract=bridge.contract,
            )

    def test_contract_mismatch_is_rejected_before_brain_use(self):
        bridge = make_bridge()
        bad = HostEvent(
            contract_sha256="0" * 64,
            event_id="wrong-contract",
            observations={"signal": 1.0},
        )
        with self.assertRaises(ValueError):
            bridge.experience(bad)
        self.assertEqual(bridge.bound_brain.count, 0)

if __name__ == "__main__":
    unittest.main()
