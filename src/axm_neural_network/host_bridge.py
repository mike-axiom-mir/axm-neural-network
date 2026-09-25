from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Optional

BRIDGE_SCHEMA = "axm-host-brain-bridge/v2"
EXPERIENCE_SCHEMA = "axm-host-experience/v2"
ACTION_SCHEMA = "axm-host-action-proposal/v2"
STATE_REF_SCHEMA = "axm-host-brain-state-ref/v2"
ROOT_REF_SCHEMA = "axm-root-contract-ref/v1"

AXM_ROOT_CONTRACT_REF = {
    "schema": ROOT_REF_SCHEMA,
    "owner_repo": "mike-axiom-mir/axm-neural-brain",
    "owner_commit": "30f485cd725e0e22b4a72c45cdbc62a908284c30",
    "contract_schema": "axm-roots/v0.1",
    "contract_sha256": "7d1eaeb05ce9353bccb5783a045ce9be91bf327c17bd93b47fdb68fd6bc46ed2",
}

AUTHORITY_BOUNDARY = {
    "permissions": "host",
    "persistence": "host",
    "observations": "host",
    "execution": "host",
}


def canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("bridge payload must be strict JSON") from exc


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
        canonical_bytes(body)

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
            "root_contract": deepcopy(AXM_ROOT_CONTRACT_REF),
        }

    @property
    def fingerprint(self) -> str:
        return sha256_json(self.to_dict())

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
            for name, value in event.target.items():
                _finite(value, f"target {name}")
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


class HostBrainBridge:
    """Adapts host observations to a brain without owning learned state."""

    def __init__(self, bound_brain, contract: BridgeContract):
        if bound_brain.contract.to_dict() != dict(contract.brain_io):
            raise ValueError("bound brain I/O contract does not match bridge contract")
        if bound_brain.contract.fingerprint != contract.brain_io_sha256:
            raise ValueError("bound brain I/O fingerprint does not match bridge contract")
        self.bound_brain = bound_brain
        self.contract = contract

    def experience(self, event: HostEvent) -> ActionProposal:
        self.contract.validate_event(event)
        target = None
        if event.target is not None:
            target = [float(event.target[name]) for name in self.contract.output_names]
        raw_output = self.bound_brain.experience(
            event.observations,
            target=target,
            reward=event.reward,
            source=event.source,
            tag=event.tag,
            directions=event.directions,
        )
        values = self.bound_brain.output_state(raw_output)
        return ActionProposal(
            contract_sha256=self.contract.fingerprint,
            event_id=event.event_id,
            values=values,
        )

    def export_state_reference(self, state_ref: str) -> dict:
        if not isinstance(state_ref, str) or not state_ref or state_ref.strip() != state_ref:
            raise ValueError("state_ref must be non-empty trimmed text")
        brain_snapshot = self.bound_brain.to_snapshot()
        body = {
            "schema": STATE_REF_SCHEMA,
            "contract_sha256": self.contract.fingerprint,
            "brain_io_sha256": self.contract.brain_io_sha256,
            "brain_state_sha256": sha256_json(brain_snapshot),
            "state_ref": state_ref,
            "contains_neural_state": False,
            "host_owned_persistence": True,
            "execution_authorized": False,
        }
        return {"body": body, "sha256": sha256_json(body)}

    @classmethod
    def restore_from_host_state(
        cls,
        receipt: Mapping[str, object],
        *,
        restored_bound_brain,
        expected_contract: BridgeContract,
    ) -> "HostBrainBridge":
        if not isinstance(receipt, Mapping):
            raise ValueError("state-reference receipt must be a mapping")
        body = receipt.get("body")
        digest = receipt.get("sha256")
        if not isinstance(body, Mapping) or not isinstance(digest, str):
            raise ValueError("state-reference receipt must contain body and sha256")
        if sha256_json(body) != digest:
            raise ValueError("state-reference receipt integrity check failed")
        if body.get("schema") != STATE_REF_SCHEMA:
            raise ValueError("unsupported state-reference schema")
        if body.get("contains_neural_state") is not False:
            raise ValueError("bridge state-reference must not contain neural state")
        if body.get("host_owned_persistence") is not True:
            raise ValueError("host must own neural persistence")
        if body.get("execution_authorized") is not False:
            raise ValueError("bridge cannot grant execution authority")
        if body.get("contract_sha256") != expected_contract.fingerprint:
            raise ValueError("state reference belongs to another bridge contract")
        if body.get("brain_io_sha256") != expected_contract.brain_io_sha256:
            raise ValueError("state reference brain I/O mismatch")
        actual = sha256_json(restored_bound_brain.to_snapshot())
        if body.get("brain_state_sha256") != actual:
            raise ValueError("restored host-owned brain state does not match reference")
        return cls(restored_bound_brain, expected_contract)
