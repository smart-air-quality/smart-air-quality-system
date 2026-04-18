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

    # Count cities with worse AQI (higher = worse air quality)
    worse_cities = sum(1 for v in aqis if v > local_aqi)
    better_cities = sum(1 for v in aqis if v < local_aqi)
    rank = better_cities + 1  # rank 1 = best (lowest AQI), rank N = worst
    
    # Percentage of cities that have worse air quality than local
    pct_worse = round((worse_cities / len(aqis)) * 100, 1) if aqis else 0.0
    # Note: percentile_clean stores % of cities worse than local (for backward compatibility)
    pct_clean = pct_worse

    raw = (local_aqi / g_avg - 1) * 50 + 50 if g_avg else 50
    score = round(max(0.0, min(100.0, raw)), 1)
    level = "Normal" if score < 45 else ("Elevated" if score < 70 else "Critical")

    direction = (
        "better than" if local_aqi < g_avg else
        "equal to" if local_aqi == int(g_avg) else
        "worse than"
    )
    
    # Summary: make it clear whether local is better or worse
    if pct_worse >= 50:
        summary = (
            f"Local AQI {local_aqi} is {direction} the global average ({g_avg}). "
            f"Better air quality than {pct_worse}% of {len(aqis)} sampled cities."
        )
    else:
        pct_better = round((better_cities / len(aqis)) * 100, 1) if aqis else 0.0
        summary = (
            f"Local AQI {local_aqi} is {direction} the global average ({g_avg}). "
            f"Worse air quality than {pct_better}% of {len(aqis)} sampled cities."
        )

    return ComparisonResult(
        local_aqi=local_aqi, city_aqi=city_aqi,
        global_avg_aqi=g_avg, global_min_aqi=g_min, global_max_aqi=g_max,
        global_rank=rank, total_cities=len(aqis),
        percentile_clean=pct_clean,
        awareness_score=score, awareness_level=level,
        summary=summary,
    )
