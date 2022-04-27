from tools.mon import Threshold, Range, Status, PerformanceLabel
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
        r = Range('5.0:')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, 5)
        self.assertEqual(r.end, float('inf'))
        self.assertTrue(r.outside)

        self.assertTrue(r.check(4))
        self.assertFalse(r.check(5))
        self.assertFalse(r.check(6))

    def test_no_start(self):
        r = Range('~:5.0')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, float('-inf'))
        self.assertEqual(r.end, 5)
        self.assertTrue(r.outside)

        self.assertFalse(r.check(4))
        self.assertFalse(r.check(5))
        self.assertTrue(r.check(6))

    def test_inside(self):
        r = Range('@2:4.0')
        self.assertTrue(isinstance(r, Range))
        self.assertEqual(r.start, float('2'))
        self.assertEqual(r.end, float('4'))
        self.assertFalse(r.outside)

        self.assertFalse(r.check(1.99))
        self.assertTrue(r.check(2))
        self.assertTrue(r.check(3.5))
        self.assertTrue(r.check(4))
        self.assertFalse(r.check(4.1))

    def test_invalid(self):
        with self.assertRaises(Exception):
            Range('a')
        with self.assertRaises(Exception):
            Range('a:b')
        with self.assertRaises(Exception):
            Range('~:b')
        with self.assertRaises(Exception):
            Range(':1')
        with self.assertRaises(Exception):
            Range('1:~')
        with self.assertRaises(Exception):
            Range('1,1:1,2')

class TestThreshold(unittest.TestCase):
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
        self.assertEqual(t.get_status([95]), Status.CRITICAL)
        t = Threshold(critical="@5:9", warning="@20:25")
        self.assertEqual(t.get_status([5]), Status.CRITICAL)
        self.assertEqual(t.get_status([9]), Status.CRITICAL)
        self.assertEqual(t.get_status([4]), Status.OK)
        self.assertEqual(t.get_status([10]), Status.OK)
        self.assertEqual(t.get_status([20]), Status.WARNING)
        self.assertEqual(t.get_status([22]), Status.WARNING)
        self.assertEqual(t.get_status([25]), Status.WARNING)
        self.assertEqual(t.get_status([25.1]), Status.OK)
        self.assertEqual(t.get_status([19.9]), Status.OK)
        self.assertEqual(t.get_status([4,10,5]), Status.CRITICAL)
        t = Threshold()
        self.assertEqual(t.get_status([42]), Status.OK)

class TestPerfromanceLabel(unittest.TestCase):
    def test_a(self):
        p = PerformanceLabel(
            label = 'a b',
            value = 9.0,
            uom = 'kB',
            warning = '15',
            critical = '90:',
            min=0,
            max=100,
        )
        self.assertEqual(str(p), "'a b'=9.0kB;15;90:;0;100")
        p = PerformanceLabel(
            label = 'a b',
            value = 9.0,
            uom = 'kB',
        )
        self.assertEqual(str(p), "'a b'=9.0kB;;;;")
        p = PerformanceLabel(
            label = 'a\nb',
            value = 9.0,
            uom = 'kB',
            threshold=Threshold(warning='15', critical='90:')
        )
        self.assertEqual(str(p), "'a b'=9.0kB;15;90:;;")