import unittest

from axm_neural_network import EventEnvelope, LocalBus, NodeDescriptor, NodeIdentity


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.bus = LocalBus()
        self.bus.register(NodeDescriptor(NodeIdentity("a"), "contract-a"))
        self.bus.register(NodeDescriptor(NodeIdentity("b"), "contract-a"))

    def test_unavailable_node(self):
        self.bus.registry.set_available("b", False)
        event = EventEnvelope("a", "b", 0, "experience", "contract-a", {})
        self.assertEqual(self.bus.accept(event), "UNAVAILABLE")

    def test_interface_mismatch(self):
        event = EventEnvelope("a", "b", 0, "experience", "contract-b", {})
        self.assertEqual(self.bus.accept(event), "INCOMPATIBLE_CONTRACT")


if __name__ == "__main__":
    unittest.main()
