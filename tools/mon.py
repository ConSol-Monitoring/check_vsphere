OK      = 0
WARNING = 1
ERROR   = 2
UNKNOWN = 3

class Range:
    """
    Class to handle Range specs like :10 or ~:10 or 10:20 and the like
    https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT
    """
    def __init__(self, range_spec):
        self.range_spec = range_spec
        self.start = None
        self.end = None
        self.outside = True
        self._parse_range()

    def _parse_range(self):
        if not self.range_spec:
            return

        try:
            self.end = float(str(self.range_spec))
            self.start = 0.0
        except Exception:
            (self.start, self.end) = self.range_spec.split(':')
            if self.start.startswith("@"):
                self.outside  = False
                self.start = self.start[1:]

            if self.start == '~':
                self.start = float('-inf')
            if self.end == '':
                self.end = float('inf')

            # finally start and end musst be floats
            self.start = float(self.start)
            self.end = float(self.end)

    def check(self,value):
        """
        checks value against rangespec
        return True if it should alert and False if not
        """
        r = False

        if float(value) < self.start or float(value) > self.end:
            r = True

        if not self.outside:
            return not r

        return r

class Threshold:
    def __init__(self, warning=None, critical=None):
        self.warning = warning
        self.critical = critical

    def get_status(values):
        for v in values:
            pass


# @dataclass would be nice, but it's python >= 3.7
# customers still have 3.6 a lot
class PerformanceValue:
    def __init__(self, label, value, uom=None, threshold=None, warning=None, critical=None, min=None, max=None):
        self.label = label
        self.value = value
        self.uom = uom
        self.warning = warning
        self.critical = critical
        self.threshold = threshold
        self.min = min
        self.max = max

        if threshold:
            self.warning = threshold.warning
            self.critical = threshold.critical
        else:
            self.threshold = Threshold(warning, critical)