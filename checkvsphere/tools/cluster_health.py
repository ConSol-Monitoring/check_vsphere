import unittest
from monplugin import Status
from typing import List


def check_cluster_health(failed: int, members: int, thresholds: List[str]) -> Status:
    def parse_threshold(t_str: str) -> tuple:
        """Parse threshold string and return (max_members, warn_str, crit_str)."""
        parts = t_str.split(":")

        if len(parts) == 3:
            try:
                max_m = int(parts[0])
            except ValueError:
                raise ValueError(f"Invalid max_members value: '{parts[0]}'")
            return (max_m, parts[1], parts[2])
        elif len(parts) == 2:
            return (float("inf"), parts[0], parts[1])
        else:
            raise ValueError(f"Malformed threshold string: '{t_str}'")

    def resolve_value(s: str) -> float:
        """Resolve a threshold value (can be a number or percentage)."""
        s = s.strip()
        if s.endswith("%"):
            return (float(s[:-1]) / 100.0) * members
        return float(s)

    # Parse and validate all thresholds
    parsed = {}
    for t_str in thresholds:
        max_m, warn_str, crit_str = parse_threshold(t_str)

        if max_m in parsed:
            label = (
                "Fallback (Infinity)"
                if max_m == float("inf")
                else f"max_members {max_m}"
            )
            raise ValueError(f"Duplicate threshold configuration found for {label}")

        parsed[max_m] = (warn_str, crit_str)

    if float("inf") not in parsed:
        raise ValueError(
            "No fallback threshold (Infinity) provided in thresholds list."
        )

    # Select the tightest threshold applicable to `members`
    warn_str, crit_str = parsed[min(m for m in parsed if m >= members)]

    # Compare failed count against resolved limits
    if failed >= resolve_value(crit_str):
        return Status.CRITICAL
    if failed >= resolve_value(warn_str):
        return Status.WARNING
    return Status.OK


class TestThreshold(unittest.TestCase):
    def test_it(self):
        thresholds = ["3:1:1", "4:1:2", "5:1:2", "10:1:30%", "3:30%"]
        self.assertEqual(check_cluster_health(0, 1, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 2, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 3, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 4, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 5, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 6, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 9, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 10, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 11, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(1, 11, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(0, 100, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(1, 100, thresholds), Status.OK)
        self.assertEqual(check_cluster_health(2, 100, thresholds), Status.OK)

        self.assertEqual(check_cluster_health(1, 4, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(1, 5, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(1, 6, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(1, 9, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(1, 10, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(2, 10, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(3, 100, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(28, 100, thresholds), Status.WARNING)
        self.assertEqual(check_cluster_health(29, 100, thresholds), Status.WARNING)

        self.assertEqual(check_cluster_health(1, 1, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(2, 1, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(1, 2, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(9, 3, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(2, 4, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(3, 4, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(3, 4, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(2, 5, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(3, 5, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(3, 10, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(30, 100, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(39, 100, thresholds), Status.CRITICAL)
        self.assertEqual(check_cluster_health(1000, 100, thresholds), Status.CRITICAL)

        self.assertEqual(check_cluster_health(0, 10, ["1:100%"]), Status.OK)
        self.assertEqual(check_cluster_health(1, 10, ["1:100%"]), Status.WARNING)
        self.assertEqual(check_cluster_health(1, 1, ["1:100%"]), Status.CRITICAL)

    def test_duplicate_error(self):
        with self.assertRaises(ValueError):
            check_cluster_health(0, 5, ["10:1:2", "10:2:3", "5:6"])
        with self.assertRaises(ValueError):
            check_cluster_health(0, 5, ["10:1:2", "2:3", "5:6"])

    def test_too_large_warn(self):
        self.assertEqual(check_cluster_health(2, 10, ["20:10%"]), Status.CRITICAL)

    def test_missing_fallback_error(self):
        with self.assertRaises(ValueError):
            check_cluster_health(0, 5, ["10:1:2"])
        with self.assertRaises(ValueError):
            check_cluster_health(0, 5, ["10:1:2", "20:2:3"])
