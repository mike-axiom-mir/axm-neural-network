# AXM Neural Network

**Status: PRODUCTION / HEAVY EXPERIMENTAL**

Research and executable experiments for neural mechanisms, framework boundaries,
and possible AXM-owned substrate work. The existing local coordination package
is retained alongside that research; it does not own a brain's learned state.

## Local coordination

`src/axm_neural_network` provides explicit node identities and interfaces,
per-source/target ordering, accepted-event deduplication and conflict detection,
bounded queues, backpressure, capability routing, handler-failure results, and
hashed snapshots of pending queues and availability. Accepted history is detached
from caller and handler mutations. Execution is in process and host supplied.

Messages and contracts may move between nodes. The bus does not silently average,
merge, synchronize, or replace learned weights. Its state is separate from neural
parameters and host-owned brain persistence.

## Research

- [AXM Hybrid Brain — Long-Term End Goal](research/AXM_HYBRID_BRAIN_END_GOAL.md)
- [Neural Substrate + Hybrid Architecture Findings](research/NEURAL_SUBSTRATE_HYBRID_FINDINGS.md)

- [Micro-Simulation Learning Substrate](research/MICROSIMULATION_LEARNING_SUBSTRATE.md) — backend-independent primitives for cheap replayable state transitions, batched simulation, direct neural experience, adaptive simulation selection, and measured throughput.

Framework-backed experiments remain useful while AXM keeps architecture,
experience, provenance, behavioral evidence, and backend boundaries explicit.
This repository does not claim to replace PyTorch or JAX.

## Verification

The [minimal neural substrate experiment](SUBSTRATE.md) adds interchangeable
Python-list and optional NumPy calculators, inspected gradients, momentum-state
restore and held-out learning evidence. It remains separate from coordination.

With the sibling brain checkout available:

`PYTHONPATH=src:../axm-neural-brain python -m unittest discover -s tests -v`

Named tests establish bounded mechanics, not general intelligence or distributed
network readiness. See [STATUS.md](STATUS.md) for the coordination scope.

Truth before story. Agency / non-domination. Continuity. Wisdom before speed.

Required Notice: Copyright 2026 Mike - Axiom/Mir.
