"""Pure deterministic two-value dynamics, with optional vectorized stepping.

This is a numeric micro-simulation, not a physical-world claim. One transition
updates position and velocity through two declared tanh equations.
"""
from dataclasses import asdict, dataclass
from copy import deepcopy
import math
import random

from .substrate import _digest, _finite


@dataclass(frozen=True)
class DynamicsRules:
    position_decay: float = .6
    velocity_coupling: float = .2
    action_gain: float = .5
    horizon: int = 12

    def __post_init__(self):
        for key in ('position_decay', 'velocity_coupling', 'action_gain'):
            value = _finite(getattr(self, key), key)
            if abs(value) > 1:
                raise ValueError('reference dynamics coefficients must be in [-1, 1]')
        if type(self.horizon) is not int or self.horizon < 1:
            raise ValueError('horizon must be a positive integer')

    @property
    def fingerprint(self):
        return _digest(asdict(self))


@dataclass(frozen=True)
class DynamicsState:
    position: float
    velocity: float
    step: int
    seed: int
    rules_sha256: str


class MicroDynamics:
    simulator_id = 'axm.micro-dynamics'
    version = '1'
    experience_source = 'deterministic_simulation'

    def __init__(self, rules=None, *, backend='python'):
        self.rules = rules if rules is not None else DynamicsRules()
        if not isinstance(self.rules, DynamicsRules):
            raise ValueError('explicit DynamicsRules required')
        if backend not in ('python', 'numpy'):
            raise ValueError('backend must be python or numpy')
        self.backend = backend
        if backend == 'numpy':
            try:
                import numpy
            except ImportError as exc:
                raise RuntimeError('NumPy micro-simulation requested but unavailable') from exc
            self.np = numpy

    def reset(self, seed):
        if type(seed) is not int:
            raise ValueError('seed must be an integer')
        rng = random.Random(seed)
        return DynamicsState(rng.uniform(-1,1), rng.uniform(-1,1), 0, seed, self.rules.fingerprint)

    def _validate_state(self, state):
        if not isinstance(state, DynamicsState) or state.rules_sha256 != self.rules.fingerprint:
            raise ValueError('state belongs to different dynamics rules')
        if type(state.seed) is not int or type(state.step) is not int or not 0 <= state.step <= self.rules.horizon:
            raise ValueError('invalid seed or step counter')
        for key in ('position', 'velocity'):
            if abs(_finite(getattr(state,key),key)) > 1:
                raise ValueError('state values outside [-1, 1]')

    def snapshot(self, state):
        self._validate_state(state)
        body = {'schema':'axm.micro-state/v1', 'simulator_id':self.simulator_id,
                'version':self.version, 'rules':asdict(self.rules), 'state':asdict(state)}
        return {'body':body,'sha256':_digest(body)}

    def restore(self, snapshot):
        body = deepcopy(snapshot['body'])
        if _digest(body) != snapshot.get('sha256') or body.get('schema') != 'axm.micro-state/v1':
            raise ValueError('state snapshot integrity or schema mismatch')
        if body.get('simulator_id') != self.simulator_id or body.get('version') != self.version or body.get('rules') != asdict(self.rules):
            raise ValueError('state snapshot simulator mismatch')
        state = DynamicsState(**body['state'])
        self._validate_state(state)
        return state

    def step_many(self, states, actions):
        if not isinstance(states, (list,tuple)) or not states or len(states) != len(actions):
            raise ValueError('batch requires aligned nonempty states and actions')
        checked = []
        for state, action in zip(states,actions):
            self._validate_state(state)
            if state.step >= self.rules.horizon:
                raise ValueError('terminal state requires an explicit reset')
            value = _finite(action,'action')
            if abs(value) > 1: raise ValueError('action outside [-1, 1]')
            checked.append(value)
        r = self.rules
        if self.backend == 'numpy':
            x = self.np.asarray([s.position for s in states],dtype=self.np.float64)
            v = self.np.asarray([s.velocity for s in states],dtype=self.np.float64)
            a = self.np.asarray(checked,dtype=self.np.float64)
            positions = self.np.tanh(r.position_decay*x+r.velocity_coupling*v+r.action_gain*a).tolist()
            velocities = self.np.tanh(-r.velocity_coupling*x+.7*v+.3*a).tolist()
        else:
            positions = [math.tanh(r.position_decay*s.position+r.velocity_coupling*s.velocity+r.action_gain*a)
                         for s,a in zip(states,checked)]
            velocities = [math.tanh(-r.velocity_coupling*s.position+.7*s.velocity+.3*a)
                          for s,a in zip(states,checked)]
        results = []
        for state, action, position, velocity in zip(states,checked,positions,velocities):
            after = DynamicsState(position, velocity, state.step+1, state.seed, r.fingerprint)
            body = {'schema':'axm.micro-experience/v1', 'experience_source':self.experience_source,
                    'simulator_id':self.simulator_id,'simulator_version':self.version,
                    'backend':self.backend, 'parameters':asdict(r),'seed':state.seed,
                    'before':asdict(state),'action':action,'after':asdict(after),
                    'observation':[state.position,state.velocity,action],
                    'target':[position,velocity],'terminal':after.step==r.horizon}
            results.append({'state':after,'experience':{'body':body,'sha256':_digest(body)}})
        return results

    def step(self, state, action):
        return self.step_many([state],[action])[0]

    def verify_transition(self, experience):
        body = deepcopy(experience['body'])
        if _digest(body) != experience.get('sha256'):
            raise ValueError('experience hash mismatch')
        before = DynamicsState(**body['before'])
        # Exact replay checks all fields, including source classification.
        expected = self.step(before, body['action'])['experience']
        if expected != experience:
            raise ValueError('experience is not an exact transition of this simulator')
        return body
