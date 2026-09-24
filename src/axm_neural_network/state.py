from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .bus import LocalBus
from .model import EventEnvelope, NodeDescriptor, NodeIdentity, sha256_value

NETWORK_SNAPSHOT_SCHEMA = "axm.neural-network.snapshot/v1"


def _descriptor_to_dict(descriptor: NodeDescriptor) -> dict[str, Any]:
    return {
        "node_id": descriptor.identity.node_id,
        "lineage": descriptor.identity.lineage,
        "interface_fingerprint": descriptor.interface_fingerprint,
        "brain_fingerprint": descriptor.brain_fingerprint,
        "capabilities": list(descriptor.capabilities),
    }


def _descriptor_from_dict(value: Mapping[str, Any]) -> NodeDescriptor:
    return NodeDescriptor(
        identity=NodeIdentity(value["node_id"], value["lineage"]),
        interface_fingerprint=value["interface_fingerprint"],
        brain_fingerprint=value.get("brain_fingerprint"),
        capabilities=tuple(value.get("capabilities", ())),
    )


def _payload_without_digest(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    body = deepcopy(dict(snapshot))
    body.pop("sha256", None)
    return body


def capture_network(bus: LocalBus) -> dict[str, Any]:
    nodes = [
        _descriptor_to_dict(bus.registry.nodes[node_id])
        for node_id in sorted(bus.registry.nodes)
    ]
    pending = {
        node_id: [event.to_dict() for event in bus.queues[node_id].items]
        for node_id in sorted(bus.queues)
        if bus.queues[node_id].items
    }
    body = {
        "schema": NETWORK_SNAPSHOT_SCHEMA,
        "queue_limit": bus.queue_limit,
        "nodes": nodes,
        "availability": {
            node_id: bool(bus.registry.available[node_id])
            for node_id in sorted(bus.registry.available)
        },
        "accepted_events": [event.to_dict() for event in bus.event_log],
        "pending": pending,
        "next_sequence": [
            {
                "source_node": source,
                "target_node": target,
                "next": sequence,
            }
            for (source, target), sequence in sorted(bus.next_sequence.items())
        ],
        "accepted_fingerprints": {
            key: bus.seen[key] for key in sorted(bus.seen)
        },
        "truth_boundary": {
            "contains_neural_weights": False,
            "network_owns_learned_state": False,
            "host_execution_authority": False,
        },
    }
    return {**body, "sha256": sha256_value(body)}


def restore_network(snapshot: Mapping[str, Any]) -> LocalBus:
    if not isinstance(snapshot, Mapping):
        raise ValueError("network snapshot must be a mapping")
    raw = dict(snapshot)
    if raw.get("schema") != NETWORK_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported network snapshot schema")
    digest = raw.get("sha256")
    if not isinstance(digest, str) or digest != sha256_value(_payload_without_digest(raw)):
        raise ValueError("network snapshot integrity check failed")

    queue_limit = raw.get("queue_limit")
    if not isinstance(queue_limit, int) or isinstance(queue_limit, bool) or queue_limit <= 0:
        raise ValueError("invalid queue limit")

    bus = LocalBus(queue_limit)
    nodes = raw.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("nodes must be a list")
    for node_raw in nodes:
        descriptor = _descriptor_from_dict(node_raw)
        if bus.register(descriptor) != "REGISTERED":
            raise ValueError("node registration conflict during restore")

    availability = raw.get("availability")
    if not isinstance(availability, Mapping) or set(availability) != set(bus.registry.nodes):
        raise ValueError("availability does not match registered nodes")
    for node_id, available in availability.items():
        if not isinstance(available, bool):
            raise ValueError("availability values must be booleans")
        bus.registry.set_available(node_id, available)

    accepted_raw = raw.get("accepted_events")
    if not isinstance(accepted_raw, list):
        raise ValueError("accepted_events must be a list")
    accepted = [EventEnvelope.from_dict(item) for item in accepted_raw]

    expected_by_pair: dict[tuple[str, str], int] = {}
    accepted_fingerprints: dict[str, str] = {}
    for event in accepted:
        pair = (event.source_node, event.target_node)
        expected = expected_by_pair.get(pair, 0)
        if event.sequence != expected:
            raise ValueError("accepted event history is not contiguous")
        if event.source_node not in bus.registry.nodes or event.target_node not in bus.registry.nodes:
            raise ValueError("accepted event references unknown node")
        target = bus.registry.nodes[event.target_node]
        if event.interface_fingerprint != target.interface_fingerprint:
            raise ValueError("accepted event contract no longer matches target")
        if event.event_key in accepted_fingerprints:
            raise ValueError("duplicate accepted event key")
        accepted_fingerprints[event.event_key] = event.fingerprint
        expected_by_pair[pair] = expected + 1

    declared_seen = raw.get("accepted_fingerprints")
    if declared_seen != {key: accepted_fingerprints[key] for key in sorted(accepted_fingerprints)}:
        raise ValueError("accepted fingerprint map mismatch")

    declared_next = raw.get("next_sequence")
    expected_next = [
        {"source_node": source, "target_node": target, "next": sequence}
        for (source, target), sequence in sorted(expected_by_pair.items())
    ]
    if declared_next != expected_next:
        raise ValueError("next-sequence state does not match accepted history")

    bus.event_log = accepted
    bus.seen = dict(accepted_fingerprints)
    bus.next_sequence = dict(expected_by_pair)

    pending = raw.get("pending")
    if not isinstance(pending, Mapping):
        raise ValueError("pending must be a mapping")
    pending_keys: set[str] = set()
    accepted_by_key = {event.event_key: event for event in accepted}
    accepted_order = {event.event_key: index for index, event in enumerate(accepted)}
    for node_id, items in pending.items():
        if node_id not in bus.queues or not isinstance(items, list):
            raise ValueError("pending queue references unknown node or invalid list")
        last_order = -1
        for item in items:
            event = EventEnvelope.from_dict(item)
            if event.target_node != node_id:
                raise ValueError("pending event target does not match queue")
            canonical = accepted_by_key.get(event.event_key)
            if canonical is None or canonical.fingerprint != event.fingerprint:
                raise ValueError("pending event is not an exact accepted event")
            if event.event_key in pending_keys:
                raise ValueError("pending event appears more than once")
            order = accepted_order[event.event_key]
            if order <= last_order:
                raise ValueError("pending queue order does not match accepted order")
            last_order = order
            pending_keys.add(event.event_key)
            if not bus.queues[node_id].put(event):
                raise ValueError("pending queue exceeds configured limit")

    return bus
