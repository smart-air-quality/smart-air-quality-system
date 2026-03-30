"""
Local vs Regional vs Global air quality comparison.
Computes ranking, percentile, and awareness score.
"""

from dataclasses import dataclass
from statistics import mean, stdev


@dataclass
class ComparisonResult:
    local_aqi: int
    city_aqi: int | None
    global_avg_aqi: float
    global_min_aqi: int
    global_max_aqi: int
    global_rank: int          # 1 = cleanest
    total_cities: int
    percentile_clean: float   # 0-100, higher = cleaner than X% of cities
    awareness_score: float    # 0-100, higher = more polluted relative to world
    awareness_level: str      # "Normal" | "Elevated" | "Critical"
    comparison_summary: str


def compute_comparison(local_aqi: int, city_aqi: int | None,
                        global_samples: list[dict]) -> ComparisonResult:
    """
    Compare local AQI against city-level and global samples.

    global_samples: list of dicts with at least {"city": str, "aqi": int|float}
    """
    valid_aqis = [
        int(s["aqi"]) for s in global_samples
        if s.get("aqi") is not None
    ]

    if not valid_aqis:
        valid_aqis = [50, 60, 80, 100, 120, 150]   # safe defaults

    global_avg = round(mean(valid_aqis), 1)
    global_min = min(valid_aqis)
    global_max = max(valid_aqis)

    # Rank: how many cities are cleaner than local?
    cleaner_count = sum(1 for v in valid_aqis if v < local_aqi)
    rank = cleaner_count + 1
    percentile_clean = round((len(valid_aqis) - cleaner_count) / len(valid_aqis) * 100, 1)

    # Awareness score: how much worse than global average (capped 0-100)
    if global_avg > 0:
        raw_score = (local_aqi / global_avg - 1) * 50 + 50
    else:
        raw_score = 50
    awareness_score = round(max(0.0, min(100.0, raw_score)), 1)

    if awareness_score < 45:
        level = "Normal"
    elif awareness_score < 70:
        level = "Elevated"
    else:
        level = "Critical"

    # Summary text
    city_part = f"city AQI {city_aqi}" if city_aqi else "no city data"
    if local_aqi < global_avg:
        direction = f"better than the global average ({global_avg})"
    elif local_aqi == int(global_avg):
        direction = f"equal to the global average ({global_avg})"
    else:
        direction = f"worse than the global average ({global_avg})"

    summary = (
        f"Local AQI {local_aqi} is {direction}. "
        f"Compared to {len(valid_aqis)} cities worldwide, "
        f"your location is cleaner than {percentile_clean}% of them."
    )

    return ComparisonResult(
        local_aqi=local_aqi,
        city_aqi=city_aqi,
        global_avg_aqi=global_avg,
        global_min_aqi=global_min,
        global_max_aqi=global_max,
        global_rank=rank,
        total_cities=len(valid_aqis),
        percentile_clean=percentile_clean,
        awareness_score=awareness_score,
        awareness_level=level,
        comparison_summary=summary,
    )
