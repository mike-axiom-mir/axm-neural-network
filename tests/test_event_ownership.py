import unittest

from axm_neural_network import (
    EventEnvelope, LocalBus, NodeDescriptor, NodeIdentity,
    capture_network, restore_network,
)


class EventOwnershipTests(unittest.TestCase):
    def bus(self):
        bus = LocalBus()
        for name in ('a', 'b'):
            bus.register(NodeDescriptor(NodeIdentity(name), 'contract'))
        return bus

    def test_caller_cannot_rewrite_accepted_nested_payload(self):
        bus = self.bus()
        payload = {'nested': {'values': [1, 2]}}
        event = EventEnvelope('a', 'b', 0, 'experience', 'contract', payload)
        self.assertEqual(bus.accept(event), 'ACCEPTED')
        payload['nested']['values'].append(3)
        event.data['nested']['values'].append(4)
        exported = event.to_dict()
        exported['data']['nested']['values'].append(5)
        snapshot = capture_network(bus)
        restored = restore_network(snapshot)
        self.assertEqual(restored.pop('b').data, {'nested': {'values': [1, 2]}})
        original = EventEnvelope('a', 'b', 0, 'experience', 'contract', {'nested': {'values': [1, 2]}})
        self.assertEqual(bus.accept(original), 'DUPLICATE')

    def test_delivered_event_cannot_rewrite_accepted_history(self):
        bus = self.bus()
        bus.accept(EventEnvelope('a', 'b', 0, 'experience', 'contract', {'items': [1]}))
        delivered = bus.pop('b')
        delivered.data['items'].append(2)
        restored = restore_network(capture_network(bus))
        self.assertEqual(restored.event_log[0].data, {'items': [1]})
        self.assertIsNone(restored.pop('b'))

    def test_captured_payload_is_detached_from_live_bus(self):
        bus = self.bus()
        bus.accept(EventEnvelope('a', 'b', 0, 'experience', 'contract', {'items': [1]}))
        snapshot = capture_network(bus)
        snapshot['accepted_events'][0]['data']['items'].append(2)
        self.assertEqual(bus.event_log[0].data, {'items': [1]})
        self.assertEqual(bus.pop('b').data, {'items': [1]})

    def test_boolean_sequence_is_rejected(self):
        with self.assertRaises(ValueError):
            EventEnvelope('a', 'b', True, 'experience', 'contract', {})

    def test_duplicate_registration_preserves_unavailable_state(self):
        bus = self.bus()
        bus.registry.set_available('b', False)
        self.assertEqual(bus.register(bus.registry.nodes['b']), 'REGISTERED')
        self.assertFalse(bus.registry.available['b'])
