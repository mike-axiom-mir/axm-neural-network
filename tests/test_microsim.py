from copy import deepcopy
from dataclasses import replace
import importlib.util
import unittest

from axm_neural_network.microsim import MicroDynamics, DynamicsRules
from axm_neural_network.substrate import _digest


class MicroSimulationTests(unittest.TestCase):
    def test_pure_batch_matches_scalar_and_replays_exactly(self):
        sim = MicroDynamics()
        states = [sim.reset(seed) for seed in (1,2,3)]
        before = deepcopy(states)
        actions = [-.8,.2,.7]
        batched = sim.step_many(states,actions)
        scalar = [sim.step(s,a) for s,a in zip(states,actions)]
        self.assertEqual(batched,scalar)
        self.assertEqual(states,before)
        for result in batched:
            body = sim.verify_transition(result['experience'])
            self.assertEqual(body['experience_source'],'deterministic_simulation')
            self.assertEqual(sim.restore(sim.snapshot(result['state'])),result['state'])

    def test_wrong_rules_nonfinite_and_terminal_rejected(self):
        sim = MicroDynamics(DynamicsRules(horizon=1))
        state = sim.reset(7)
        for action in (True, float('nan'), float('inf'), 1.1):
            with self.assertRaises(ValueError): sim.step(state,action)
        with self.assertRaises(ValueError): MicroDynamics().step(state,.2)
        terminal = sim.step(state,.2)['state']
        with self.assertRaises(ValueError): sim.step(terminal,.2)
        with self.assertRaises(ValueError): sim.step(replace(state,step=True),.2)

    def test_rehashed_source_or_transition_lies_fail_replay(self):
        sim = MicroDynamics()
        record = sim.step(sim.reset(3),.2)['experience']
        for key,bad in [('experience_source','external_observation'),('target',[0,0]),('terminal',True),('seed',999)]:
            altered = deepcopy(record)
            altered['body'][key] = bad
            altered['sha256'] = _digest(altered['body'])
            with self.assertRaises(ValueError): sim.verify_transition(altered)

    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'optional NumPy backend absent')
    def test_vector_backend_matches_reference_with_declared_tolerance(self):
        reference, vector = MicroDynamics(), MicroDynamics(backend='numpy')
        states = [reference.reset(seed) for seed in range(32)]
        actions = [(i-16)/16 for i in range(32)]
        left,right = reference.step_many(states,actions),vector.step_many(states,actions)
        for a,b in zip(left,right):
            self.assertAlmostEqual(a['state'].position,b['state'].position,places=14)
            self.assertAlmostEqual(a['state'].velocity,b['state'].velocity,places=14)
            self.assertEqual(b['experience']['body']['backend'],'numpy')
            vector.verify_transition(b['experience'])


if __name__ == '__main__': unittest.main()
