from dataclasses import dataclass
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


def _text(label: str, value: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{label} must be non-empty and trimmed")
    return value


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be strict canonical JSON") from exc


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        if not isinstance(self.data, Mapping):
            raise ValueError("data must be a mapping")
        canonical_bytes(dict(self.data))
        object.__setattr__(self, "data", deepcopy(dict(self.data)))
        if self.parent_event_key is not None:
            _text("parent_event_key", self.parent_event_key)

    @property
    def event_key(self) -> str:
        return f"{self.source_node}>{self.target_node}:{self.sequence}"

    @property
    def fingerprint(self) -> str:
        return sha256_value(
            {
                "source_node": self.source_node,
                "target_node": self.target_node,
                "sequence": self.sequence,
                "kind": self.kind,
                "interface_fingerprint": self.interface_fingerprint,
                "data": dict(self.data),
                "parent_event_key": self.parent_event_key,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_node": self.source_node,
            "target_node": self.target_node,
            "sequence": self.sequence,
            "kind": self.kind,
            "interface_fingerprint": self.interface_fingerprint,
            "data": deepcopy(dict(self.data)),
            "parent_event_key": self.parent_event_key,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EventEnvelope":
        return cls(
            source_node=value["source_node"],
            target_node=value["target_node"],
            sequence=value["sequence"],
            kind=value["kind"],
            interface_fingerprint=value["interface_fingerprint"],
            data=value["data"],
            parent_event_key=value.get("parent_event_key"),
        )


@dataclass(frozen=True)
class Receipt:
    ordinal: int
    action: str
    status: str
    node_id: str | None = None
    event_key: str | None = None
    detail: str = ""
