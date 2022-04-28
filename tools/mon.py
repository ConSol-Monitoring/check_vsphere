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

    def __repr__(self):
        return f'Range({self.range_spec})'

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

    def __repr__(self):
        return f'Threshold(critical={self.critical}, warning={self.warning})'

    def get_status(self, *args):
        for v in args:
            if self.critical and self.critical.is_set():
                if self.critical.check(v):
                    return Status.CRITICAL
        for v in args:
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

    def __repr__(self):
        return f'PerformanceLabel({str(self)})'


class Check:
    def __init__(self, shortname='unknown', threshold=None):
        self.shortname = shortname
        self.set_threshold(threshold)
        self._perfdata = []
        self._messages = {
            Status.OK: [],
            Status.WARNING: [],
            Status.CRITICAL: [],
        }

    def set_threshold(self, threshold=None, **kwargs):
        if threshold:
            if isinstance(threshold, Threshold):
                self.threshold = threshold
            else:
                raise ValueError('threshold must be a Threshold object')
        else:
            self.threshold = Threshold(**kwargs)

    def add_message(self, status, *messages):
        if isinstance(status, str):
            status = Status[status]

        for m in messages:
            self._messages[status].append(m)

    def add_perfdata(self, **kwargs):
        self._perfdata.append( PerformanceLabel(**kwargs) )


    def check_messages(self, separator=' '):
        code = Status.OK

        if self._messages[Status.CRITICAL]:
            code = Status.CRITICAL
        elif self._messages[Status.WARNING]:
            code = Status.WARNING

        return (code, separator.join(self._messages[code]))

    def check_threshold(self, *args):
        return self.threshold.get_status(*args)

    def exit(self, code=Status.OK, message="OK"):
        if isinstance(code, str):
            code = Status[code]

        print("{name} {code} - {text}".format(
            name=self.shortname,
            code=code.name,
            text=message
        ))

        if self._perfdata:
            print("| ", end='')
            print('\n'.join([ str(x) for x in self._perfdata ]))

        raise SystemExit(code.value)
