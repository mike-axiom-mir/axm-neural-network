# Replayable numeric simulation providers

`axm_neural_network.simulation_contract` supplies a small shared contract for
Brain sessions and UC adapters. It does not import either consumer.

A provider declares its identity, version, backend, dimensions, scalar action
bounds, finite horizon and explicit deterministic-simulation source in
`describe_space()`. It implements `reset`, `step`, `snapshot`, `restore` and
`verify_transition`. State snapshots expose `body.state`; transition packets
expose `before`, `after`, `observation`, `target`, `action`, `seed` and `terminal`.
`MicroDynamics` implements this protocol without changing its equations.

`verified_transition` validates numeric dimensions and provenance, checks the
packet digest, and requires complete replay verification from the provider.
It rejects a relabeled external observation even if someone recalculates its
hash. The host must still supply trusted provider code: this is a data contract,
not a sandbox or independent proof of the provider's physics.

The reusable persistent learning session lives in `axm-neural-brain`; UC's
canvas-fitting adapter lives in `axm-uc-neural`. Numeric shapes are declared,
rather than hardcoded to the original three-input/two-output dynamics example.

Validation: `PYTHONPATH=src:<brain-checkout> python -m unittest discover -s tests -v`.
