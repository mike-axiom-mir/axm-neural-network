from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Type

from .contract import (
    CHECKPOINT_SCHEMA,
    ActionProposal,
    BridgeContract,
    HostEvent,
    sha256_json,
)


class HostBrainBridge:
    """Explicit host<->brain adapter.

    The bridge passes named host observations and optional teaching signals into
    a bound brain, then returns named advisory outputs. It does not decide host
    permissions, persistence policy, observations, or execution.
    """

    def __init__(self, bound_brain, contract: BridgeContract):
        donor_contract = bound_brain.contract.to_dict()
        if donor_contract != dict(contract.brain_io):
            raise ValueError("bound brain I/O contract does not match bridge contract")
        if bound_brain.contract.fingerprint != contract.brain_io_sha256:
            raise ValueError("bound brain I/O fingerprint does not match bridge contract")
        self.bound_brain = bound_brain
        self.contract = contract

    def experience(self, event: HostEvent) -> ActionProposal:
        self.contract.validate_event(event)
        target = None
        if event.target is not None:
            target = [
                float(event.target[name])
                for name in self.contract.output_names
            ]
        raw_output = self.bound_brain.experience(
            event.observations,
            target=target,
            reward=event.reward,
            source=event.source,
            tag=event.tag,
            directions=event.directions,
        )
        values = self.bound_brain.output_state(raw_output)
        if set(values) != set(self.contract.output_names):
            raise ValueError("brain returned output channels outside the contract")
        return ActionProposal(
            contract_sha256=self.contract.fingerprint,
            event_id=event.event_id,
            values=values,
        )

    def export_checkpoint(self) -> dict:
        body = {
            "schema": CHECKPOINT_SCHEMA,
            "contract": self.contract.to_dict(),
            "contract_sha256": self.contract.fingerprint,
            "bound_brain": self.bound_brain.to_snapshot(),
        }
        return {
            "body": deepcopy(body),
            "sha256": sha256_json(body),
        }

    @classmethod
    def restore(
        cls,
        checkpoint: Mapping[str, object],
        *,
        bound_brain_type: Type,
        expected_contract: BridgeContract | None = None,
    ) -> "HostBrainBridge":
        if not isinstance(checkpoint, Mapping):
            raise ValueError("checkpoint must be a mapping")
        body = checkpoint.get("body")
        digest = checkpoint.get("sha256")
        if not isinstance(body, Mapping) or not isinstance(digest, str):
            raise ValueError("checkpoint must contain body and sha256")
        if sha256_json(body) != digest:
            raise ValueError("bridge checkpoint integrity check failed")
        if body.get("schema") != CHECKPOINT_SCHEMA:
            raise ValueError("unsupported bridge checkpoint schema")
        contract = BridgeContract.from_dict(body["contract"])
        if body.get("contract_sha256") != contract.fingerprint:
            raise ValueError("bridge checkpoint contract fingerprint mismatch")
        if expected_contract is not None and contract.fingerprint != expected_contract.fingerprint:
            raise ValueError("checkpoint belongs to a different bridge contract")
        bound_brain = bound_brain_type.from_snapshot(body["bound_brain"])
        return cls(bound_brain, contract)
