# Micro-Simulation Learning Substrate

**Status: research architecture / not yet an earned capability**

This note defines the lower-level neural/runtime side of a simulation-first AXM learning loop.

The purpose is not to build one giant world simulator. It is to make **small, cheap, repeatable state transitions** easy to run in large numbers and easy to connect directly to neural learning.

The general brain-level innovation loop belongs in `axm-neural-brain`. UC-specific simulation exposure belongs in `axm-uc-neural`. This repository focuses on the reusable substrate underneath both.

## Core idea

A useful micro-simulation can be represented as:

```text
state + action + rules + seed
        ↓
next_state + observation + outcome
```

A learner can then close the loop:

```text
observe state
-> choose action / prediction
-> simulate transition
-> receive outcome
-> update learned state
-> choose next experiment
```

The key property is **direct coupling** between simulation output and learning. The simulation is not merely rendered, logged, or converted into an offline dataset and inspected later.

## Why micro-simulations

Full environments are expensive and often contain irrelevant detail.

A micro-simulation can isolate one learnable relationship:

- memory retrieval under interference;
- routing under conflicting options;
- one procedural physics interaction;
- one resource-allocation choice;
- one graph transformation;
- one neural module under a controlled input;
- one action/consequence pair.

Cheap simulations make it possible to spend compute on **variety and iteration** instead of repeatedly rebuilding an entire world.

## Minimal simulator contract

A reusable substrate can start with a tiny interface:

```text
reset(seed, parameters) -> state, observation

step(state, action) ->
    next_state,
    observation,
    outcome,
    terminal,
    diagnostics
```

Useful optional operations:

```text
snapshot(state)
restore(snapshot)
describe_space()
validate_action(action)
verify_transition(before, action, after)
```

The simulator does not decide how the learner is trained. It exposes grounded state transitions.

## Pure-state path first

Where practical, the cheapest simulators should be expressible as pure or near-pure state transitions:

```text
next_state = transition(state, action, seed)
```

Benefits:

- easier deterministic replay;
- easier parallel execution;
- easier batching;
- easier comparison across neural candidates;
- fewer hidden side effects;
- simpler provenance.

Not every useful environment will fit this model. It is a preferred fast path, not a universal requirement.

## Batch and vectorized execution

The substrate should permit many independent simulator instances to advance together:

```text
[state_1, state_2, ... state_N]
        +
[action_1, action_2, ... action_N]
        ↓
batched transition
        ↓
[next_state_1, ... next_state_N]
```

Frameworks such as JAX or PyTorch may be useful for vectorized execution, but the AXM contract should remain backend-independent.

The runtime must measure actual throughput on the available hardware. It must not infer performance from the existence of batching alone.

## Adaptive rather than fixed simulation

A fixed simulation batch is useful for early testing, but the deeper target is a closed loop.

```text
learner state at t
-> select simulation family / parameters
-> run experience
-> learner updates
-> learner state at t+1
-> next simulation choice changes
```

This makes simulation selection itself learnable.

A future selector can choose simulations based on:

- uncertainty;
- repeated error;
- disagreement between internal predictions;
- novelty relative to prior experience;
- expected information gain;
- prior transfer success.

Those signals must be tested empirically; their names alone do not prove they improve learning.

## Experience packet

Every simulation-to-learning handoff should preserve enough information to reconstruct cause:

```json
{
  "experience_source": "deterministic_simulation",
  "simulator_id": "...",
  "simulator_version": "...",
  "seed": 0,
  "parameters": {},
  "state_before_ref": "...",
  "observation": "...",
  "action": "...",
  "prediction": "...",
  "state_after_ref": "...",
  "outcome": "...",
  "verification": "...",
  "learner_checkpoint_before": "...",
  "learner_checkpoint_after": "...",
  "runtime_environment": "..."
}
```

The exact serialization is intentionally not fixed yet.

## Experience source separation

The substrate should preserve whether an event came from:

```text
external_observation
deterministic_simulation
procedural_simulation
learned_world_model
replay
imported_dataset
```

This prevents a learned rollout from silently becoming evidence about external reality.

It also permits separate weighting or training policies later if experiments show that different source types should be treated differently.

## Learned world models are a later layer

A neural world model can eventually predict state transitions and generate internal rollouts.

That opens a second loop:

```text
external / deterministic experience
-> train world model
-> world model generates candidate rollouts
-> learner trains / plans against rollouts
-> real or deterministic environment checks transfer
-> world model error becomes new learning signal
```

The world model must remain corrigible by grounded outcomes.

A model prediction is not a fact simply because another neural component consumed it.

## Simulation as neural-architecture laboratory

The same substrate can test neural variants:

```text
one parent checkpoint
        ↓
candidate A  candidate B  candidate C
        ↓        ↓           ↓
same simulation distribution
        ↓        ↓           ↓
direct learning
        ↓        ↓           ↓
held-out comparison
```

This supports the Neural Innovation Engine without requiring every candidate to interact with an expensive external environment.

The comparison should distinguish:

- immediate task performance;
- learning speed;
- sample efficiency;
- compute cost;
- memory cost;
- retained behavior after restart;
- held-out generalization;
- regression on earlier capabilities.

## Learning the experiment policy

The most important later benchmark is not raw simulator count.

It is whether the learner gets better at **spending a fixed simulation budget**.

A minimal experiment:

1. Define several simulation families.
2. Define a fixed number of simulation steps.
3. Compare random family selection with a fixed curriculum.
4. Train a small selector using previous experiment outcomes.
5. Give each method the same simulation budget.
6. Compare held-out behavior.
7. Repeat across multiple Genesis seeds/checkpoints.

The narrow claim to earn is:

> prior experience can improve which simulations are selected next.

## Throughput accounting

The substrate should report at least:

- state transitions per second;
- complete episodes per second;
- average steps per episode;
- simulator CPU time;
- learner-update CPU/GPU time;
- peak RAM/VRAM;
- bytes written;
- batch size;
- duplicate-state or duplicate-experience rate where detectable.

A phrase such as "millions of simulations" is meaningless without the size of one simulation and the measured throughput.

A one-step integer state machine and a rendered 3D environment are both simulations, but they are not comparable units of work.

## Resource-bounded operation

Simulation should consume an explicit resource budget rather than an open-ended mandate to maximize activity.

A run can be bounded by one or more of:

```text
max_transitions
max_episodes
max_wall_time
max_cpu_time
max_gpu_time
max_memory
max_storage_write
```

The learner may choose how to use the budget within the experiment contract.

## Reproducibility

For deterministic simulations, store enough information to replay exact transitions:

- simulator version;
- seed;
- initial state;
- parameters;
- action sequence;
- backend/runtime version.

For neural learning runs, also retain:

- Genesis or parent checkpoint;
- optimizer/learning-rule configuration;
- random seeds;
- framework/runtime versions;
- hardware details where relevant.

Bit-for-bit repeatability may not always be achievable on accelerated neural backends. The evidence target should therefore include behavioral reproducibility, not only identical bytes.

## First implementation target

Do not begin with a general-purpose simulator engine.

Build one tiny end-to-end reference path:

```text
small deterministic simulator
-> batched runner
-> experience packet
-> tiny learner
-> persistent checkpoint
-> held-out behavioral test
```

Then measure:

1. whether direct simulated experience changes later behavior;
2. whether learned state survives restart;
3. actual transitions/second;
4. whether larger batches improve throughput on the chosen backend;
5. whether the learner generalizes to unseen simulator seeds.

Only after this works should the substrate generalize into a reusable simulation fabric.

## Relationship to AXM Neural Brain

`axm-neural-brain` owns the persistent learner and the higher-level question:

> Which experiment should I run next, and what neural change should I test?

This repository supplies reusable execution primitives for running those experiments efficiently.

## Relationship to UC Neural

`axm-uc-neural` can adapt UC capabilities and deterministic workflows into concrete simulator families.

This repository should not contain UC-specific creation logic.

## Evidence boundary

This architecture does not prove that AXM can currently perform high-throughput simulation, that simulation-driven learning will outperform external-only learning, or that a learned experiment policy will discover useful neural innovations.

Those are experimental claims to earn with measured runs.

Required Notice: Copyright 2026 Mike - Axiom/Mir.
