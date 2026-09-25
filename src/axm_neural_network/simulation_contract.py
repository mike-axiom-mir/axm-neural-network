"""Small host/provider contract for numeric, replayable simulation experience.

Validation is structural, not a sandbox: the host chooses trusted providers.
No learner or UC dependency is required to produce or inspect a transition.
"""
from copy import deepcopy
import math

from .substrate import _digest


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def describe(provider):
    spec = deepcopy(provider.describe_space())
    if not isinstance(spec, dict) or spec.get('schema') != 'axm.simulation-space/v1':
        raise ValueError('unsupported simulation space')
    for key in ('simulator_id', 'version', 'backend'):
        if not isinstance(spec.get(key), str) or not spec[key]:
            raise ValueError(f'missing simulation {key}')
    for key in ('observation_size', 'target_size', 'horizon'):
        if type(spec.get(key)) is not int or not 1 <= spec[key] <= 1024:
            raise ValueError(f'invalid simulation {key}')
    bounds = spec.get('action_bounds')
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError('scalar action bounds required')
    low, high = [finite(v, 'action bound') for v in bounds]
    if low >= high:
        raise ValueError('action bounds must increase')
    if spec.get('experience_source') != 'deterministic_simulation':
        raise ValueError('this contract requires deterministic simulation provenance')
    _digest(spec)
    return spec


def verified_transition(provider, packet, *, spec=None):
    spec = describe(provider) if spec is None else spec
    if not isinstance(packet, dict) or not isinstance(packet.get('body'), dict):
        raise ValueError('simulation packet must contain an object body')
    body = deepcopy(packet['body'])
    if packet.get('sha256') != _digest(body):
        raise ValueError('simulation packet integrity mismatch')
    for key, expected in (('simulator_id', spec['simulator_id']),
                          ('simulator_version', spec['version']),
                          ('backend', spec['backend']),
                          ('experience_source', spec['experience_source'])):
        if body.get(key) != expected:
            raise ValueError(f'simulation packet {key} mismatch')
    if type(body.get('seed')) is not int or type(body.get('terminal')) is not bool:
        raise ValueError('simulation packet seed/terminal invalid')
    for key, size in (('observation', spec['observation_size']), ('target', spec['target_size'])):
        if not isinstance(body.get(key), list) or len(body[key]) != size:
            raise ValueError(f'simulation packet {key} dimensions mismatch')
        for value in body[key]:
            finite(value, key)
    action = finite(body.get('action'), 'action')
    if not spec['action_bounds'][0] <= action <= spec['action_bounds'][1]:
        raise ValueError('simulation action outside declared bounds')
    if provider.verify_transition(deepcopy(packet)) != body:
        raise ValueError('provider replay did not verify the complete packet')
    return body
