import unittest
from monplugin import Status


def check_cluster_health(failed: int, members: int, thresholds: list[str]) -> Status:
    parsed_thresholds = []
    seen_max_members = set()
    has_fallback = False

    # Thresholds are of the form: max_members:warn:crit
    # or warn:crit (this one is required as a fallback)
    # it just means: +Inf:warn:crit basically
    for t_str in thresholds:
        parts = t_str.split(":")

        if len(parts) == 3:
            try:
                max_m = int(parts[0])
            except ValueError:
                raise ValueError(f"Invalid max_members value: '{parts[0]}'")
            w_val, c_val = parts[1], parts[2]
        elif len(parts) == 2:
            max_m = float("inf")
            w_val, c_val = parts[0], parts[1]
            has_fallback = True
        else:
            raise ValueError(f"Malformed threshold string: '{t_str}'")

        if max_m in seen_max_members:
            label = (
                "Fallback (Infinity)"
                if max_m == float("inf")
                else f"max_members {max_m}"
            )
            raise ValueError(f"Duplicate threshold configuration found for {label}")

        seen_max_members.add(max_m)
        parsed_thresholds.append((max_m, w_val, c_val))

    if not has_fallback:
        raise ValueError(
            "No fallback threshold (Infinity) provided in thresholds list."
        )

    # filter out the thresholds where max_members is too small
    eligible = [t for t in parsed_thresholds if t[0] >= members]
    # take the one with the smallest max_values
    selected = min(eligible, key=lambda x: x[0])

    _, warn_str, crit_str = selected

    def resolve_threshold(val_str: str) -> float:
        if "%" in val_str:
            percentage = float(val_str.strip("%")) / 100.0
            return percentage * members
        return float(val_str)

    crit_limit = resolve_threshold(crit_str)
    warn_limit = resolve_threshold(warn_str)

    if failed >= crit_limit:
        return Status.CRITICAL
    if failed >= warn_limit:
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
