from copy import deepcopy
import unittest

from axm_neural_network.microsim import MicroDynamics
from axm_neural_network.simulation_contract import describe, verified_transition
from axm_neural_network.substrate import _digest


class SimulationContractTests(unittest.TestCase):
    def test_existing_provider_advertises_dimensions_and_replays(self):
        provider = MicroDynamics()
        self.assertEqual(describe(provider)['observation_size'], 3)
        packet = provider.step(provider.reset(7), .5)['experience']
        self.assertEqual(verified_transition(provider, packet), packet['body'])

    def test_rehashed_invalid_numeric_and_source_packets_rejected(self):
        provider = MicroDynamics()
        packet = provider.step(provider.reset(7), .5)['experience']
        for field, value in [('observation',[1,2]), ('target',[True,0]),
                             ('experience_source','external_run'), ('seed',True),
                             ('action',2), ('terminal',1)]:
            forged = deepcopy(packet)
            forged['body'][field] = value
            forged['sha256'] = _digest(forged['body'])
            with self.assertRaises(ValueError):
                verified_transition(provider, forged)

    def test_invalid_or_changed_provider_space_is_rejected(self):
        provider = MicroDynamics()
        spec = describe(provider)
        spec['horizon'] = True
        provider.describe_space = lambda: spec
        with self.assertRaises(ValueError): describe(provider)
