import sys


__version__ = '0.1'

# Clocks
try:
    # Python 3.3+ (PEP 418)
    from time import monotonic as monotonic_clock, perf_counter
except ImportError:
    import time

    monotonic_clock = time.time
    if sys.platform == "win32":
        perf_counter = time.clock
    else:
        perf_counter = time.time


# Statistics
try:
    from statistics import mean, stdev as _stdev   # Python 3.4+

    def stdev(data):
        # Wrapper to hide the xbar parameter, to be portable with Python 2
        return _stdev(data)
except ImportError:
    import math

    def mean(data):
        if not data:
            raise ValueError("data must be non-empty")
        return float(sum(data)) / len(data)

    def stdev(data):
        data = [float(value) for value in data]
        n = len(data)
        if n < 2:
            raise ValueError('stdev requires at least two data points')

        c = mean(data)

        total = sum((x - c) ** 2 for x in data)
        total2 = sum((x - c) for x in data)
        ss = total - total2**2 / n
        variance = ss / (n - 1)

        return math.sqrt(variance)


class Result:
    def __init__(self, values=None, name=None, metadata=None):
        self.values = []
        if values:
            self.values.extend(values)
        self.name = name
        # Raw metadata dictionary, key=>value, keys and values are non-empty
        # strings
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}

    def mean(self):
        return mean(self.values)

    def stdev(self):
        return stdev(self.values)

    def _format(self):
        text = str(self.mean())
        if len(self.values) >= 2:
            text = "%s +- %s" % (text, self.stdev())
        return text

    def __str__(self):
        text = self._format()
        if self.name:
            text = '%s: %s' % (self.name, text)
        return text

    def merge_result(self, result):
        self.values.extend(result.values)
        if self.name is None:
            self.name = result.name
        self.metadata.update(result.metadata)
