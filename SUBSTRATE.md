# Minimal neural substrate experiment

`axm_neural_network.substrate` is a small independent neural calculator. It does
not replace the recurrent `AXMBrain`, the coordination bus, or a general framework.

It implements one dense hidden tanh layer, tanh outputs, half mean squared error,
and momentum SGD. All gradients are computed from the pre-update parameters.
The Python-list backend is AXM-owned. The optional NumPy float64 backend computes
the same equations using matrix operations and acts as an independent comparison.

```python
from axm_neural_network.substrate import DenseConfig, DenseModel

model = DenseModel(DenseConfig(2, 8, 1, seed=7), parameter_budget=1000)
genesis = model.snapshot()
model.train_batch([[0.2, -0.4], [-0.5, 0.7]], [[0.6], [-0.3]])
learned = model.snapshot()
restored = DenseModel.restore(learned)
# Optional explicit calculator switch; learned parameters and momentum survive.
array_model = DenseModel.restore(learned, backend="numpy")
```

Prediction has no recurrent side effects. The complete batch is validated before
parameters or optimizer state change. Snapshots carry configuration, equation
version, backend, parameters, momentum and step count. Restoring rejects a bad
digest, dimensions, nonfinite numbers and invalid state even if the outer hash
has been recomputed. Hashes provide integrity checking, not authentication.

The host chooses a parameter budget; models that exceed it are refused before
parameter allocation. The library does not read or write checkpoints on its own,
start training on import, select a backend silently, or grant execution authority.

## Evidence

- Every analytic parameter gradient compared with central finite differences.
- Thirty optimizer updates compared between list and NumPy backends, including
  predictions, gradients, parameters and momentum (13 decimal places in the local
  float64 fixture; not a universal cross-hardware bitwise guarantee).
- Retained held-out improvement on a synthetic tanh relationship.
- Exact same-backend future trajectory after restoring optimizer and model state.
- Malformed later batch entries leave the entire state unchanged.
- Explicit cross-backend state migration, structural corruption rejection and
  host parameter-budget checks.

Run the substrate tests without the separate brain repository:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_substrate.py -v
```

NumPy is optional locally. The parity test reports a skip when absent; CI installs
NumPy 2.3.5 and executes it. A parity skip does not establish backend equivalence.
Python 3.11+ is required. No GPU, JAX, MLX, PyTorch, acceleration or large-model
performance claim is made.

Full coordination and bridge verification additionally requires a sibling checkout
of `axm-neural-brain`:

```sh
PYTHONPATH=src:../axm-neural-brain python -m unittest discover -s tests -v
```

CI pins the integrity-tested core commit explicitly. The existing host bridge
keeps learned-state storage with the host and sends references and fingerprints.
The new calculator is not automatically wired into that bridge or into UC.

## Direct micro-simulation path

`axm_neural_network.microsim` implements the first bounded path from the newer
[micro-simulation proposal](research/MICROSIMULATION_LEARNING_SUBSTRATE.md).
It supplies pure seeded reset, state snapshot/restore, scalar and batched stepping,
terminal checks and exact transition evidence. Every packet is explicitly labeled
`deterministic_simulation`; replay rejects a rehashed packet that claims to be an
external observation. Python and optional NumPy float64 paths share the contract.

The unit is a two-value tanh state transition, not a rendered scene or validated
physics model. The brain repository's `neural.axm_brain.simulation` consumes these
packets directly, updates an isolated brain, and tests predictions on unseen seeds.

```sh
PYTHONPATH=src python verification/benchmark_microsim.py --output micro-throughput.json
```

The local receipt measured roughly 14,300–19,700 transitions/second including
validation and hashed packets. Batches improved each backend's throughput in this
run, but NumPy remained slower than Python for this small unit. No acceleration
claim is inferred from vectorization. The receipt includes all three timing trials
for batch sizes 1, 32 and 128, CPU time, and a separate Python-allocation sample.
That allocation sample is not total process RAM or VRAM. The simulator writes no
files; only the explicit benchmark CLI writes its requested receipt.

Adaptive simulation-family selection and learned world models remain future work.
