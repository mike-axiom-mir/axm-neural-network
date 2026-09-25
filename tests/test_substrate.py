from copy import deepcopy
import importlib.util
import math
import unittest

from axm_neural_network.substrate import DenseConfig, DenseModel, _digest


class SubstrateTests(unittest.TestCase):
    def model(self, **kwargs):
        return DenseModel(DenseConfig(2, 3, 2, seed=71, learning_rate=.08, momentum=.7), **kwargs)

    def test_every_gradient_matches_numerical_difference(self):
        model = self.model()
        x, target = [.31, -.42], [.6, -.2]
        _, gradient = model.loss_gradient(x, target)
        for j, analytic in enumerate(gradient):
            p = model.parameters[j]
            model.parameters[j] = p + 1e-6
            upper = model.loss_gradient(x, target)[0]
            model.parameters[j] = p - 1e-6
            lower = model.loss_gradient(x, target)[0]
            model.parameters[j] = p
            self.assertAlmostEqual(analytic, (upper-lower)/2e-6, places=8)

    def test_learning_improves_held_out_behavior_and_retains_trajectory(self):
        model = DenseModel(DenseConfig(1, 5, 1, seed=11, learning_rate=.15, momentum=.3))
        train = [[-.9], [-.5], [-.1], [.3], [.7]]
        targets = [[math.tanh(1.4*x[0]-.2)] for x in train]
        held = [[-.7], [.1], [.5], [.9]]
        def error(m):
            return sum((m.predict(x)[0]-math.tanh(1.4*x[0]-.2))**2 for x in held)/len(held)
        before = error(model)
        for _ in range(200): model.train_batch(train, targets)
        self.assertLess(error(model), before*.1)
        restored = DenseModel.restore(model.snapshot())
        for _ in range(10):
            model.train_batch(train, targets)
            restored.train_batch(train, targets)
        self.assertEqual(model.snapshot(), restored.snapshot())

    def test_invalid_later_batch_item_preserves_complete_state(self):
        model = self.model()
        before = model.snapshot()
        for bad in ([float('nan'), 0], [True, 0], [0], [float('inf'), 0]):
            with self.assertRaises(ValueError):
                model.train_batch([[0, 1], bad], [[1, 0], [0, 1]])
            self.assertEqual(before, model.snapshot())

    def test_same_seed_and_explicit_resource_budget(self):
        self.assertEqual(self.model().snapshot(), self.model().snapshot())
        with self.assertRaises(ValueError): self.model(parameter_budget=1)
        with self.assertRaises(ValueError): DenseModel(DenseConfig(True, 3, 2))

    def test_restore_rejects_rehashed_structural_and_optimizer_corruption(self):
        model = self.model()
        for field, bad in [('parameters', [0.0]), ('velocity', [0.0]), ('steps', True), ('backend', 'guess'), ('equations', 'different')]:
            snap = deepcopy(model.snapshot())
            snap['body'][field] = bad
            snap['sha256'] = _digest(snap['body'])
            with self.assertRaises(ValueError): DenseModel.restore(snap)

    def test_exported_state_and_prediction_do_not_mutate_model(self):
        model = self.model()
        before = model.snapshot()
        exported = model.snapshot()
        exported['body']['parameters'][0] += 1
        model.predict([.1, .2])
        self.assertEqual(before, model.snapshot())

    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'optional numpy backend absent')
    def test_numpy_parity_and_explicit_backend_migration(self):
        first = self.model()
        second = DenseModel.restore(first.snapshot(), backend='numpy')
        xs, ys = [[.2, -.5], [.8, .3]], [[-.7, .1], [.4, -.6]]
        for _ in range(30):
            for a, b in zip(first.predict(xs[0]), second.predict(xs[0])):
                self.assertAlmostEqual(a, b, places=13)
            loss1, gradient1 = first.loss_gradient(xs[0], ys[0])
            loss2, gradient2 = second.loss_gradient(xs[0], ys[0])
            self.assertAlmostEqual(loss1, loss2, places=13)
            for a, b in zip(gradient1, gradient2): self.assertAlmostEqual(a, b, places=13)
            first.train_batch(xs, ys)
            second.train_batch(xs, ys)
        for a, b in zip(first.parameters, second.parameters): self.assertAlmostEqual(a, b, places=13)
        for a, b in zip(first.velocity, second.velocity): self.assertAlmostEqual(a, b, places=13)
        migrated = DenseModel.restore(second.snapshot(), backend='python')
        self.assertEqual(migrated.parameters, second.parameters)
        self.assertEqual(migrated.velocity, second.velocity)
        self.assertEqual(migrated.steps, second.steps)


if __name__ == '__main__':
    unittest.main()
