import enum
from distutils.log import WARN
from logging import CRITICAL


class Status(enum.Enum):
    OK       = 0
    WARNING  = 1
    CRITICAL = 2
    UNKNOWN  = 3

class Range:
    def __init__(self, range_spec=None):
        """
        Handle Range specs like :10, ~:10, 10:20 or @1.0:1.5 and the like. See:
        https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT
        """
        self.range_spec = range_spec
        self.start = None
        self.end = None
        self.outside = True
        self._parse_range()

    def __str__(self):
        return self.range_spec or ""

    def is_set(self):
        return self.range_spec is not None

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

        if not self.range_spec:
            return r

        if float(value) < self.start or float(value) > self.end:
            r = True

        if not self.outside:
            return not r

        return r

class Threshold:
    def __init__(self, warning=None, critical=None):
        self.warning = warning if isinstance(warning, Range) else Range(warning)
        self.critical = critical if isinstance(critical, Range) else Range(critical)

    def get_status(self,values):
        for v in values:
            if self.critical and self.critical.is_set():
                if self.critical.check(v):
                    return Status.CRITICAL
        for v in values:
            if self.warning and self.warning.is_set():
                if self.warning.check(v):
                    return Status.WARNING


        return Status.OK


# @dataclass would be nice, but it's python >= 3.7
# customers still have 3.6 a lot
class PerformanceLabel:
    def __init__(self, label, value, uom=None, threshold=None, warning=None, critical=None, min=None, max=None):
        self.label = label
        self.value = float(value)
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

        self.label = self.label.replace('\n', ' ')

        if "'" in label or "=" in label:
            raise ValueError("label contains illegal characters: " + label)

    def __str__(self):
        d = dict()
        for k,v in self.__dict__.items():
            d[k] = v if v is not None else ''

        return "'{label}'={value}{uom};{warning};{critical};{min};{max}".format( **d )
