"""UTC ISO timestamps (requires NTP sync via ntptime)."""

try:
    import ntptime
except ImportError:
    ntptime = None


def sync_ntp(max_retries=3):
    if ntptime is None:
        return False
    for _ in range(max_retries):
        try:
            ntptime.settime()
            return True
        except OSError:
            pass
    return False


def utc_iso():
    import time

    try:
        t = time.time()
        sec = int(t)
        ms = int((t - sec) * 1000)
    except (OSError, TypeError):
        sec = 0
        ms = 0
    tup = time.gmtime(sec)
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}Z".format(
        tup[0],
        tup[1],
        tup[2],
        tup[3],
        tup[4],
        tup[5],
        ms,
    )
