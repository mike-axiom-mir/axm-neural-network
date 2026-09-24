from .model import EventEnvelope
from .queue import LocalQueue
from .registry import NodeRegistry


class LocalBus:
    def __init__(self, queue_limit: int = 32):
        self.registry = NodeRegistry()
        self.queue_limit = queue_limit
        self.queues = {}
        self.next_sequence = {}
        self.seen = set()
        self.event_log = []

    def register(self, descriptor):
        status = self.registry.register(descriptor)
        node_id = descriptor.identity.node_id
        if status == "REGISTERED" and node_id not in self.queues:
            self.queues[node_id] = LocalQueue(self.queue_limit)
        return status

    def expected_sequence(self, source_node: str, target_node: str) -> int:
        return self.next_sequence.get((source_node, target_node), 0)

    def accept(self, event: EventEnvelope) -> str:
        if event.event_key in self.seen:
            return "DUPLICATE"
        if event.source_node not in self.registry.nodes:
            return "UNKNOWN_SOURCE"
        target = self.registry.nodes.get(event.target_node)
        if target is None:
            return "UNKNOWN_TARGET"
        if not self.registry.available[event.target_node]:
            return "UNAVAILABLE"
        if event.interface_fingerprint != target.interface_fingerprint:
            return "INCOMPATIBLE_CONTRACT"
        expected = self.expected_sequence(event.source_node, event.target_node)
        if event.sequence != expected:
            return "OUT_OF_ORDER"
        if not self.queues[event.target_node].put(event):
            return "BACKPRESSURE"
        self.seen.add(event.event_key)
        self.event_log.append(event)
        self.next_sequence[(event.source_node, event.target_node)] = expected + 1
        return "ACCEPTED"

    def pop(self, node_id: str):
        queue = self.queues.get(node_id)
        if queue is None:
            return None
        return queue.get()
