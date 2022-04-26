from tools.mon import Threshold, Range, Status
import unittest

class TestRange(unittest.TestCase):
    def test_a(self):
        t = Threshold(warning="5:9")
        self.assertEqual(t.get_status([4]), Status.WARNING)
        self.assertEqual(t.get_status([10]), Status.WARNING)
        self.assertEqual(t.get_status([6]), Status.OK)
        t = Threshold(critical="5:9")
        self.assertEqual(t.get_status([4]), Status.CRITICAL)
        self.assertEqual(t.get_status([10]), Status.CRITICAL)
        self.assertEqual(t.get_status([6]), Status.OK)
        t = Threshold(critical="0:90", warning="0:80")
        self.assertEqual(t.get_status([91]), Status.CRITICAL)
        self.assertEqual(t.get_status([-1]), Status.CRITICAL)
        self.assertEqual(t.get_status([10]), Status.OK)
        self.assertEqual(t.get_status([90]), Status.WARNING)
        self.assertEqual(t.get_status([85]), Status.WARNING)
        self.assertEqual(t.get_status([95]), Status.WARNING)
