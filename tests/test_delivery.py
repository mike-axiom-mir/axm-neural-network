import unittest

from axm_neural_network.delivery import attempt
from axm_neural_network import EventEnvelope


class DeliveryTests(unittest.TestCase):
    def test_handler_failure_is_isolated(self):
        event = EventEnvelope("a", "b", 0, "experience", "contract-a", {})

        def fail(_):
            raise RuntimeError("boom")

        result = attempt(event, fail)
        self.assertEqual(result["status"], "HANDLER_FAILED")
        self.assertEqual(result["event"], event)
        self.assertEqual(result["error_type"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
