from __future__ import annotations

from .contract import BridgeContract, HostEvent

UC_ROUTE_CLASSES = (
    "COMPATIBLE_AND_SUFFICIENT",
    "COMPATIBLE_BUT_INSUFFICIENT",
    "INCOMPATIBLE",
    "UNKNOWN_HOLD",
)

UC_BRAIN_IO = {
    "schema": "axm-brain-io/v0.1",
    "name": "axm-uc-bounded-outcome/v0.1",
    "inputs": [
        {"name": "route_ready", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
        {"name": "artifact_verified", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
        {"name": "candidate_reused", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
        {"name": "ambiguity_hold", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
    ],
    "outputs": ["reuse_preference", "explore_preference"],
}

def build_uc_bridge_contract() -> BridgeContract:
    return BridgeContract(
        name="axm.uc.host-experience-reference/v1",
        brain_io=UC_BRAIN_IO,
        allow_target=True,
        allow_reward=True,
    )

def build_uc_event(
    *,
    contract: BridgeContract,
    event_id: str,
    route_class: str,
    artifact_verified: bool,
    candidate_reused: bool,
    target: dict[str, float] | None = None,
    reward: float | None = None,
    tag: str = "uc-outcome",
) -> HostEvent:
    if route_class not in UC_ROUTE_CLASSES:
        raise ValueError(f"unsupported UC route class: {route_class}")
    observations = {
        "route_ready": 1.0 if route_class == "COMPATIBLE_AND_SUFFICIENT" else 0.0,
        "artifact_verified": 1.0 if artifact_verified else 0.0,
        "candidate_reused": 1.0 if candidate_reused else 0.0,
        "ambiguity_hold": 1.0 if route_class == "UNKNOWN_HOLD" else 0.0,
    }
    return HostEvent(
        contract_sha256=contract.fingerprint,
        event_id=event_id,
        observations=observations,
        target=target,
        reward=reward,
        source="axm-uc-neural",
        tag=tag,
        directions=("CREATE",),
    )
