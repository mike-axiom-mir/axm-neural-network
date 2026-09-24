import copy
import unittest

from axm_bridge import BridgeContract, HostEvent, build_uc_bridge_contract


class BridgeContractTests(unittest.TestCase):
    def test_contract_fingerprint_is_stable(self):
        a = build_uc_bridge_contract()
        b = build_uc_bridge_contract()
        self.assertEqual(a.fingerprint, b.fingerprint)
        self.assertEqual(a.brain_io_sha256, b.brain_io_sha256)

    def test_event_fails_closed_on_contract_mismatch(self):
        contract = build_uc_bridge_contract()
        event = HostEvent(
            contract_sha256="0" * 64,
            event_id="event-1",
            observations={"route_ready": 1.0},
        )
        with self.assertRaises(ValueError):
            contract.validate_event(event)

    def test_unknown_observation_is_rejected(self):
        contract = build_uc_bridge_contract()
        event = HostEvent(
            contract_sha256=contract.fingerprint,
            event_id="event-2",
            observations={"unexpected": 1.0},
        )
        with self.assertRaises(ValueError):
            contract.validate_event(event)

    def test_partial_target_is_rejected(self):
        contract = build_uc_bridge_contract()
        event = HostEvent(
            contract_sha256=contract.fingerprint,
            event_id="event-3",
            observations={"route_ready": 1.0},
            target={"reuse_preference": 0.5},
        )
        with self.assertRaises(ValueError):
            contract.validate_event(event)

    def test_authority_boundary_is_part_of_contract_identity(self):
        contract = build_uc_bridge_contract()
        changed = copy.deepcopy(contract.to_dict())
        changed["authority"]["execution"] = "neural"
        with self.assertRaises(ValueError):
            BridgeContract.from_dict(changed)

    def test_brain_io_tamper_is_rejected(self):
        contract = build_uc_bridge_contract()
        changed = copy.deepcopy(contract.to_dict())
        changed["brain_io"]["outputs"][0] = "different-output"
        with self.assertRaises(ValueError):
            BridgeContract.from_dict(changed)


if __name__ == "__main__":
    unittest.main()
