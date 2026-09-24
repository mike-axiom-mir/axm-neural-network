import unittest

from axm_neural_network import LocalQueue


class QueueTests(unittest.TestCase):
    def test_limit_and_order(self):
        queue = LocalQueue(2)
        self.assertTrue(queue.put("a"))
        self.assertTrue(queue.put("b"))
        self.assertFalse(queue.put("c"))
        self.assertEqual(queue.get(), "a")
        self.assertEqual(queue.get(), "b")
        self.assertIsNone(queue.get())


if __name__ == "__main__":
    unittest.main()
