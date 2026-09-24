import unittest

from axm_neural_network import EventEnvelope, LocalBus, NodeDescriptor, NodeIdentity


def make_node(name):
    return NodeDescriptor(NodeIdentity(name, "test"), "contract-a")


class OrderingTests(unittest.TestCase):
    def test_order_and_duplicate(self):
        bus = LocalBus(4)
        bus.register(make_node("a"))
        bus.register(make_node("b"))
        first = EventEnvelope("a", "b", 0, "experience", "contract-a", {"n": 1})
        second = EventEnvelope("a", "b", 1, "experience", "contract-a", {"n": 2})
        self.assertEqual(bus.accept(first), "ACCEPTED")
        self.assertEqual(bus.accept(first), "DUPLICATE")
        self.assertEqual(bus.accept(second), "ACCEPTED")
        self.assertEqual(bus.pop("b").data["n"], 1)
        self.assertEqual(bus.pop("b").data["n"], 2)

    def test_gap_is_rejected(self):
        bus = LocalBus()
        bus.register(make_node("a"))
        bus.register(make_node("b"))
        event = EventEnvelope("a", "b", 1, "experience", "contract-a", {})
        self.assertEqual(bus.accept(event), "OUT_OF_ORDER")
        self.assertEqual(bus.expected_sequence("a", "b"), 0)


if __name__ == "__main__":
    unittest.main()
