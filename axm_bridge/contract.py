from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Optional

BRIDGE_SCHEMA = "axm-host-brain-bridge/v1"
EXPERIENCE_SCHEMA = "axm-host-experience/v1"
ACTION_SCHEMA = "axm-host-action-proposal/v1"
CHECKPOINT_SCHEMA = "axm-host-brain-checkpoint/v1"

AXM_ROOTS = (
    "truth",
    "agency-non-domination",
    "continuity",
    "wisdom-before-speed",
)

AUTHORITY_BOUNDARY = {
    "permissions": "host",
    "persistence": "host",
    "observations": "host",
    "execution": "host",
}

def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def _finite(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number

@dataclass(frozen=True)
class BridgeContract:
    name: str
    brain_io: Mapping[str, object]
    allow_target: bool = True
    allow_reward: bool = True
    schema: str = BRIDGE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != BRIDGE_SCHEMA:
            raise ValueError(f"unsupported bridge schema: {self.schema}")
        if not self.name or self.name.strip() != self.name:
            raise ValueError("bridge contract name must be non-empty and trimmed")
        body = dict(self.brain_io)
        if body.get("schema") != "axm-brain-io/v0.1":
            raise ValueError("bridge requires axm-brain-io/v0.1")
        inputs = body.get("inputs")
        outputs = body.get("outputs")
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("brain_io inputs must be a non-empty list")
        if not isinstance(outputs, list) or not outputs:
            raise ValueError("brain_io outputs must be a non-empty list")

    @property
    def brain_io_sha256(self) -> str:
        return sha256_json(self.brain_io)

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(str(item["name"]) for item in self.brain_io["inputs"])

    @property
    def output_names(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.brain_io["outputs"])

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "name": self.name,
            "brain_io": deepcopy(dict(self.brain_io)),
            "brain_io_sha256": self.brain_io_sha256,
            "allow_target": bool(self.allow_target),
            "allow_reward": bool(self.allow_reward),
            "authority": deepcopy(AUTHORITY_BOUNDARY),
            "roots": list(AXM_ROOTS),
        }

    @property
    def fingerprint(self) -> str:
        return sha256_json(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "BridgeContract":
        if data.get("schema") != BRIDGE_SCHEMA:
            raise ValueError("unsupported bridge contract schema")
        if data.get("authority") != AUTHORITY_BOUNDARY:
            raise ValueError("bridge authority boundary mismatch")
        if tuple(data.get("roots", ())) != AXM_ROOTS:
            raise ValueError("bridge AXM roots mismatch")
        contract = cls(
            schema=str(data["schema"]),
            name=str(data["name"]),
            brain_io=deepcopy(data["brain_io"]),
            allow_target=bool(data.get("allow_target", True)),
            allow_reward=bool(data.get("allow_reward", True)),
        )
        if data.get("brain_io_sha256") != contract.brain_io_sha256:
            raise ValueError("brain I/O contract fingerprint mismatch")
        return contract

    def validate_event(self, event: "HostEvent") -> None:
        if event.schema != EXPERIENCE_SCHEMA:
            raise ValueError("unsupported host experience schema")
        if event.contract_sha256 != self.fingerprint:
            raise ValueError("host experience contract fingerprint mismatch")
        unknown = set(event.observations) - set(self.input_names)
        if unknown:
            raise ValueError(f"unknown observation channel(s): {sorted(unknown)}")
        for name, value in event.observations.items():
            _finite(value, f"observation {name}")
        if event.target is not None:
            if not self.allow_target:
                raise ValueError("target teaching signal is disabled")
            if set(event.target) != set(self.output_names):
                raise ValueError("target must name every output channel exactly")
        if event.reward is not None:
            if not self.allow_reward:
                raise ValueError("reward teaching signal is disabled")
            _finite(event.reward, "reward")

@dataclass(frozen=True)
class HostEvent:
    contract_sha256: str
    event_id: str
    observations: Mapping[str, float]
    target: Optional[Mapping[str, float]] = None
    reward: Optional[float] = None
    source: str = "host"
    tag: str = ""
    directions: tuple[str, ...] = ()
    schema: str = EXPERIENCE_SCHEMA

@dataclass(frozen=True)
class ActionProposal:
    contract_sha256: str
    event_id: str
    values: Mapping[str, float]
    schema: str = ACTION_SCHEMA
    advisory_only: bool = True

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "contract_sha256": self.contract_sha256,
            "event_id": self.event_id,
            "values": dict(self.values),
            "advisory_only": True,
        }
