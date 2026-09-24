import unittest

from axm_neural_network import LocalBus, NodeDescriptor, NodeIdentity


class RoutingTests(unittest.TestCase):
    def test_capability_lookup_and_route_are_stable(self):
        bus = LocalBus()
        bus.register(NodeDescriptor(NodeIdentity("z"), "contract-a", capabilities=("learn",)))
        bus.register(NodeDescriptor(NodeIdentity("a"), "contract-a", capabilities=("learn",)))
        found = bus.registry.available_with("learn")
        self.assertEqual([node.identity.node_id for node in found], ["a", "z"])
        self.assertEqual(bus.first_for("learn").identity.node_id, "a")
        self.assertEqual(bus.first_for("learn", exclude_node="a").identity.node_id, "z")


if __name__ == "__main__":
    unittest.main()
