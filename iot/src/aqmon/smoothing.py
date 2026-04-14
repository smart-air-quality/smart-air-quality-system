"""Small rolling buffers for median / moving average."""


def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    if n % 2:
        return float(s[m])
    return (float(s[m - 1]) + float(s[m])) / 2.0


class RollingMedian:
    def __init__(self, size):
        self._size = max(1, int(size))
        self._buf = []

    def push(self, x):
        if x is None:
            return self.value()
        self._buf.append(float(x))
        while len(self._buf) > self._size:
            self._buf.pop(0)
        return _median(self._buf)

    def value(self):
        if not self._buf:
            return None
        return _median(self._buf)


class RollingMean:
    def __init__(self, size):
        self._size = max(1, int(size))
        self._buf = []

    def push(self, x):
        if x is None:
            return self.value()
        self._buf.append(float(x))
        while len(self._buf) > self._size:
            self._buf.pop(0)
        return sum(self._buf) / len(self._buf)

    def value(self):
        if not self._buf:
            return None
        return sum(self._buf) / len(self._buf)
