from tools.mon import Range
import unittest

class TestRange(unittest.TestCase):
    def test_num(self):
        r = Range('5')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, 0)
        self.assertEqual(r.end, 5)
        self.assertTrue(r.outside)

        self.assertTrue(r.check(-1))
        self.assertFalse(r.check(0))
        self.assertFalse(r.check(2))
        self.assertFalse(r.check(5))
        self.assertTrue(r.check(5.1))

    def test_no_end(self):
        r = Range('5:')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, 5)
        self.assertEqual(r.end, float('inf'))
        self.assertTrue(r.outside)

        self.assertTrue(r.check(4))
        self.assertFalse(r.check(5))
        self.assertFalse(r.check(6))

    def test_no_start(self):
        r = Range('~:5')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, float('-inf'))
        self.assertEqual(r.end, 5)
        self.assertTrue(r.outside)

        self.assertFalse(r.check(4))
        self.assertFalse(r.check(5))
        self.assertTrue(r.check(6))

    def test_inside(self):
        r = Range('@2:4')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, float('2'))
        self.assertEqual(r.end, float('4'))
        self.assertFalse(r.outside)

        self.assertFalse(r.check(1.99))
        self.assertTrue(r.check(2))
        self.assertTrue(r.check(3.5))
        self.assertTrue(r.check(4))
        self.assertFalse(r.check(4.1))
