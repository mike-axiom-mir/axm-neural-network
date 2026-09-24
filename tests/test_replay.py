import unittest

from axm_neural_network import EventEnvelope, LocalBus, NodeDescriptor, NodeIdentity
from axm_neural_network.replay import rebuild


def nodes():
    return (
        NodeDescriptor(NodeIdentity("a"), "contract-a"),
        NodeDescriptor(NodeIdentity("b"), "contract-a"),
    )


class ReplayTests(unittest.TestCase):
    def test_restart_replay_keeps_accepted_order(self):
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


if __name__ == "__main__":
    unittest.main()
