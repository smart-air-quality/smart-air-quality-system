"""
Local vs City vs Global AQI comparison
คำนวณ ranking, percentile, awareness score
"""

from dataclasses import dataclass
from statistics import mean


@dataclass
class ComparisonResult:
    local_aqi:         int
    city_aqi:          int | None
    global_avg_aqi:    float
    global_min_aqi:    int
    global_max_aqi:    int
    global_rank:       int
    total_cities:      int
    percentile_clean:  float
    awareness_score:   float
    awareness_level:   str    # Normal | Elevated | Critical
    summary:           str


def compute(local_aqi: int, city_aqi: int | None, global_samples: list[dict]) -> ComparisonResult:
    aqis = [int(s["aqi"]) for s in global_samples if s.get("aqi") is not None]
    if not aqis:
        aqis = [50, 60, 80, 100, 120, 150]

    g_avg = round(mean(aqis), 1)
    g_min = min(aqis)
    g_max = max(aqis)

    cleaner = sum(1 for v in aqis if v < local_aqi)
    rank = cleaner + 1
    pct_clean = round((len(aqis) - cleaner) / len(aqis) * 100, 1)

    raw = (local_aqi / g_avg - 1) * 50 + 50 if g_avg else 50
    score = round(max(0.0, min(100.0, raw)), 1)
    level = "Normal" if score < 45 else ("Elevated" if score < 70 else "Critical")

    direction = (
        "better than" if local_aqi < g_avg else
        "equal to" if local_aqi == int(g_avg) else
        "worse than"
    )
    summary = (
        f"Local AQI {local_aqi} is {direction} the global average ({g_avg}). "
        f"Cleaner than {pct_clean}% of {len(aqis)} sampled cities."
    )

    return ComparisonResult(
        local_aqi=local_aqi, city_aqi=city_aqi,
        global_avg_aqi=g_avg, global_min_aqi=g_min, global_max_aqi=g_max,
        global_rank=rank, total_cities=len(aqis),
        percentile_clean=pct_clean,
        awareness_score=score, awareness_level=level,
        summary=summary,
    )
