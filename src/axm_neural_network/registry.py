from .model import NodeDescriptor


class NodeRegistry:
    def __init__(self):
        self.nodes = {}
        self.available = {}

    def register(self, descriptor: NodeDescriptor):
        node_id = descriptor.identity.node_id
        if node_id in self.nodes and self.nodes[node_id] != descriptor:
            return "IDENTITY_CONFLICT"
        self.nodes[node_id] = descriptor
        self.available[node_id] = True
        return "REGISTERED"

    def set_available(self, node_id: str, value: bool):
        if node_id not in self.nodes:
            return "UNKNOWN_NODE"
        self.available[node_id] = bool(value)
        return "AVAILABLE" if value else "UNAVAILABLE"

    def available_with(self, capability: str):
        return tuple(
            self.nodes[node_id]
            for node_id in sorted(self.nodes)
            if self.available[node_id]
            and capability in self.nodes[node_id].capabilities
        )
