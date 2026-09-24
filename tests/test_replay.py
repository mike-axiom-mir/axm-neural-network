import copy
import unittest

from axm_neural_network import (
    EventEnvelope,
    LocalBus,
    NodeDescriptor,
    NodeIdentity,
    capture_network,
    restore_network,
)
from axm_neural_network.model import sha256_value
from axm_neural_network.replay import rebuild


def nodes():
    return (
        NodeDescriptor(NodeIdentity("a"), "contract-a"),
        NodeDescriptor(NodeIdentity("b"), "contract-a"),
    )


def _rehash(snapshot):
    body = copy.deepcopy(snapshot)
    body.pop("sha256", None)
    return {**body, "sha256": sha256_value(body)}


class ReplayTests(unittest.TestCase):
    def test_historical_rebuild_keeps_accepted_order(self):
        first = LocalBus()
        for node in nodes():
            first.register(node)
        first.accept(EventEnvelope("a", "b", 0, "experience", "contract-a", {"n": 1}))
        first.accept(EventEnvelope("a", "b", 1, "experience", "contract-a", {"n": 2}))

        replay = rebuild(nodes(), first.event_log)

        self.assertEqual(
            [event.event_key for event in replay.event_log],
            [event.event_key for event in first.event_log],
        )
        self.assertEqual(replay.expected_sequence("a", "b"), 2)

    def test_restart_restores_only_events_still_pending(self):
        first = LocalBus()
        for node in nodes():
            first.register(node)
        first.accept(EventEnvelope("a", "b", 0, "experience", "contract-a", {"n": 1}))
        first.accept(EventEnvelope("a", "b", 1, "experience", "contract-a", {"n": 2}))
        delivered = first.pop("b")
        self.assertEqual(delivered.data["n"], 1)
        first.registry.set_available("b", False)

        restored = restore_network(capture_network(first))

        self.assertFalse(restored.registry.available["b"])
        self.assertEqual(len(restored.event_log), 2)
        self.assertEqual(restored.expected_sequence("a", "b"), 2)
        self.assertEqual(restored.pop("b").data["n"], 2)
        self.assertIsNone(restored.pop("b"))

    def test_snapshot_hash_tamper_is_rejected(self):
        bus = LocalBus()
        for node in nodes():
            bus.register(node)
        snap = capture_network(bus)
        snap["availability"]["b"] = False
        with self.assertRaises(ValueError):
            restore_network(snap)

    def test_rehashed_pending_reorder_is_rejected(self):
        bus = LocalBus()
        for node in nodes():
            bus.register(node)
        bus.accept(EventEnvelope("a", "b", 0, "experience", "contract-a", {"n": 1}))
        bus.accept(EventEnvelope("a", "b", 1, "experience", "contract-a", {"n": 2}))
        snap = capture_network(bus)
        snap["pending"]["b"].reverse()
        forged = _rehash(snap)
        with self.assertRaises(ValueError):
            restore_network(forged)

    def test_non_json_event_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            EventEnvelope("a", "b", 0, "experience", "contract-a", {"bad": {1, 2}})


if __name__ == "__main__":
    unittest.main()
