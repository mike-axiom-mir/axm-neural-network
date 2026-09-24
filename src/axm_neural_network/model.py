from dataclasses import dataclass
from typing import Any, Mapping


def _text(label: str, value: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{label} must be non-empty and trimmed")
    return value


@dataclass(frozen=True, order=True)
class NodeIdentity:
    node_id: str
    lineage: str = "local"

    def __post_init__(self) -> None:
        _text("node_id", self.node_id)
        _text("lineage", self.lineage)


@dataclass(frozen=True)
class NodeDescriptor:
    identity: NodeIdentity
    interface_fingerprint: str
    brain_fingerprint: str | None = None
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("interface_fingerprint", self.interface_fingerprint)
        if self.brain_fingerprint is not None:
            _text("brain_fingerprint", self.brain_fingerprint)
        object.__setattr__(
            self,
            "capabilities",
            tuple(sorted({_text("capability", value) for value in self.capabilities})),
        )


@dataclass(frozen=True)
class EventEnvelope:
    source_node: str
    target_node: str
    sequence: int
    kind: str
    interface_fingerprint: str
    data: Mapping[str, Any]
    parent_event_key: str | None = None

    def __post_init__(self) -> None:
        _text("source_node", self.source_node)
        _text("target_node", self.target_node)
        _text("kind", self.kind)
        _text("interface_fingerprint", self.interface_fingerprint)
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise ValueError("sequence must be a non-negative integer")

    @property
    def event_key(self) -> str:
        return f"{self.source_node}>{self.target_node}:{self.sequence}"


@dataclass(frozen=True)
class Receipt:
    ordinal: int
    action: str
    status: str
    node_id: str | None = None
    event_key: str | None = None
    detail: str = ""
