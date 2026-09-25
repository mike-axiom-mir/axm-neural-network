"""Small inspectable neural calculator; independent of the coordination bus.

One hidden tanh layer, tanh outputs, half mean squared error, and momentum SGD.
The list implementation is AXM-owned. NumPy is an optional independent calculator
for the same equations, parameters and optimizer state. Neither backend owns I/O.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random


def _finite(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, not a boolean")
    return float(value)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class DenseConfig:
    inputs: int
    hidden: int
    outputs: int
    seed: int = 1
    learning_rate: float = 0.03
    momentum: float = 0.0

    @property
    def parameter_count(self):
        return self.hidden * self.inputs + self.hidden + self.outputs * self.hidden + self.outputs

    def validate(self, parameter_budget):
        for name in ("inputs", "hidden", "outputs"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")
        if type(parameter_budget) is not int or parameter_budget < 1:
            raise ValueError("parameter budget must be a positive integer")
        if self.parameter_count > parameter_budget:
            raise ValueError("model exceeds the host parameter budget")
        if _finite(self.learning_rate, "learning rate") < 0:
            raise ValueError("learning rate must be nonnegative")
        if not 0 <= _finite(self.momentum, "momentum") < 1:
            raise ValueError("momentum must be in [0, 1)")


def _unpack(config, parameters):
    i, h, o = config.inputs, config.hidden, config.outputs
    split = h * i
    w1 = [parameters[r*i:(r+1)*i] for r in range(h)]
    b1 = parameters[split:split+h]
    start = split + h
    w2 = [parameters[start+r*h:start+(r+1)*h] for r in range(o)]
    return w1, b1, w2, parameters[start+o*h:]


class PythonBackend:
    name = "python"

    def forward(self, config, parameters, observation):
        w1, b1, w2, b2 = _unpack(config, parameters)
        hidden = [math.tanh(b + sum(w*x for w, x in zip(row, observation)))
                  for row, b in zip(w1, b1)]
        output = [math.tanh(b + sum(w*x for w, x in zip(row, hidden)))
                  for row, b in zip(w2, b2)]
        return hidden, output

    def loss_gradient(self, config, parameters, observation, target):
        hidden, output = self.forward(config, parameters, observation)
        _, _, w2, _ = _unpack(config, parameters)
        delta2 = [(y-t)*(1-y*y)/config.outputs for y, t in zip(output, target)]
        delta1 = [(1-h*h)*sum(w2[o][j]*delta2[o] for o in range(config.outputs))
                  for j, h in enumerate(hidden)]
        gradient = ([d*x for d in delta1 for x in observation] + delta1
                    + [d*h for d in delta2 for h in hidden] + delta2)
        loss = sum((y-t)**2 for y, t in zip(output, target))/(2*config.outputs)
        return loss, gradient


class NumpyBackend:
    name = "numpy"

    def __init__(self):
        try:
            import numpy
        except ImportError as exc:
            raise RuntimeError("NumPy backend requested but numpy is not installed") from exc
        self.np = numpy

    def forward(self, config, parameters, observation):
        np = self.np
        w1, b1, w2, b2 = (np.asarray(v, dtype=np.float64) for v in _unpack(config, parameters))
        with np.errstate(over="raise", invalid="raise"):
            hidden = np.tanh(w1 @ np.asarray(observation, dtype=np.float64) + b1)
            output = np.tanh(w2 @ hidden + b2)
        return hidden.tolist(), output.tolist()

    def loss_gradient(self, config, parameters, observation, target):
        np = self.np
        hidden, output = self.forward(config, parameters, observation)
        hidden, output, target = (np.asarray(v, dtype=np.float64) for v in (hidden, output, target))
        w2 = np.asarray(_unpack(config, parameters)[2], dtype=np.float64)
        with np.errstate(over="raise", invalid="raise"):
            delta2 = (output-target)*(1-output*output)/config.outputs
            delta1 = (w2.T @ delta2)*(1-hidden*hidden)
            gradient = np.concatenate((np.outer(delta1, observation).ravel(), delta1,
                                       np.outer(delta2, hidden).ravel(), delta2))
            loss = float(np.mean((output-target)**2)/2)
        return loss, gradient.tolist()


def _backend(name):
    if name == "python":
        return PythonBackend()
    if name == "numpy":
        return NumpyBackend()
    raise ValueError("backend must be explicitly python or numpy")


class DenseModel:
    SCHEMA = "axm.dense-substrate/v1"

    def __init__(self, config: DenseConfig, *, backend="python", parameter_budget=100_000):
        config.validate(parameter_budget)
        self.config = config
        self.parameter_budget = parameter_budget
        self.backend = _backend(backend)
        rng = random.Random(config.seed)
        self.parameters = ([rng.uniform(-1/math.sqrt(config.inputs), 1/math.sqrt(config.inputs))
                            for _ in range(config.hidden*config.inputs)]
                           + [0.0]*config.hidden
                           + [rng.uniform(-1/math.sqrt(config.hidden), 1/math.sqrt(config.hidden))
                              for _ in range(config.outputs*config.hidden)]
                           + [0.0]*config.outputs)
        self.velocity = [0.0]*config.parameter_count
        self.steps = 0

    @staticmethod
    def _vector(value, size, name):
        if not isinstance(value, (list, tuple)) or len(value) != size:
            raise ValueError(f"{name} must have exactly {size} values")
        return [_finite(x, name) for x in value]

    def predict(self, observation):
        x = self._vector(observation, self.config.inputs, "observation")
        output = self.backend.forward(self.config, self.parameters, x)[1]
        return self._vector(output, self.config.outputs, "output")

    def loss_gradient(self, observation, target):
        x = self._vector(observation, self.config.inputs, "observation")
        y = self._vector(target, self.config.outputs, "target")
        loss, gradient = self.backend.loss_gradient(self.config, self.parameters, x, y)
        return _finite(loss, "loss"), self._vector(gradient, self.config.parameter_count, "gradient")

    def train_batch(self, observations, targets):
        if not isinstance(observations, (list, tuple)) or not observations or len(observations) != len(targets):
            raise ValueError("batch must contain aligned nonempty observations and targets")
        # Calculate and validate the complete transaction before mutating state.
        outcomes = [self.loss_gradient(x, y) for x, y in zip(observations, targets)]
        count = len(outcomes)
        gradient = [sum(g[j] for _, g in outcomes)/count for j in range(self.config.parameter_count)]
        velocity = [_finite(self.config.momentum*v + g, "optimizer update") for v, g in zip(self.velocity, gradient)]
        parameters = [_finite(p-self.config.learning_rate*v, "parameter update") for p, v in zip(self.parameters, velocity)]
        mean_loss = _finite(sum(loss for loss, _ in outcomes)/count, "batch loss")
        self.velocity, self.parameters = velocity, parameters
        self.steps += 1
        return mean_loss

    def snapshot(self):
        body = {"schema": self.SCHEMA, "config": asdict(self.config),
                "equations": "dense-tanh-tanh/half-mse/momentum-sgd/v1",
                "backend": self.backend.name, "parameters": list(self.parameters),
                "velocity": list(self.velocity), "steps": self.steps}
        return {"body": body, "sha256": _digest(body)}

    @classmethod
    def restore(cls, snapshot, *, backend=None, parameter_budget=100_000):
        value = deepcopy(snapshot)
        if not isinstance(value, dict) or set(value) != {"body", "sha256"}:
            raise ValueError("snapshot must contain body and sha256")
        body = value["body"]
        keys = {"schema", "config", "equations", "backend", "parameters", "velocity", "steps"}
        if not isinstance(body, dict) or set(body) != keys or _digest(body) != value["sha256"]:
            raise ValueError("snapshot shape or digest mismatch")
        if body["schema"] != cls.SCHEMA or body["equations"] != "dense-tanh-tanh/half-mse/momentum-sgd/v1":
            raise ValueError("snapshot equations or schema mismatch")
        if body["backend"] not in ("python", "numpy"):
            raise ValueError("unknown recorded backend")
        try:
            config = DenseConfig(**body["config"])
        except TypeError as exc:
            raise ValueError("invalid model configuration") from exc
        model = cls(config, backend=body["backend"] if backend is None else backend,
                    parameter_budget=parameter_budget)
        model.parameters = cls._vector(body["parameters"], config.parameter_count, "parameters")
        model.velocity = cls._vector(body["velocity"], config.parameter_count, "velocity")
        if type(body["steps"]) is not int or body["steps"] < 0:
            raise ValueError("step count must be a nonnegative integer")
        model.steps = body["steps"]
        return model
