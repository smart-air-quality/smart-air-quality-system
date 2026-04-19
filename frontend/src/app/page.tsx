"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

type DashboardResponse = {
  sensors?: {
    particulate_matter?: {
      pm1_0_ugm3?: number;
      pm2_5_ugm3?: number;
      pm10_ugm3?: number;
    };
    climate?: {
      temperature_c?: number;
      humidity_pct?: number;
    };
    gas?: {
      co_ppm?: number;
    };
    last_updated?: string;
    status?: string;
    message?: string;
  };
  local_aqi?: {
    aqi?: number;
    category?: string;
    health_message?: string;
  };
  comparison?: {
    city_aqi?: number;
    global_avg_aqi?: number;
    /** Legacy seeded-demo name */
    local_rank_percentile?: number;
    /** Backend v1 (`ComparisonResult`) */
    percentile_clean?: number;
  };
  trends?: {
    trend?: string;
    predicted_pm2_5_1h?: number;
    /** Backend v1 (`trends.analyze`) */
    predicted_pm25_1h?: number;
  };
  awareness?: {
    score?: number;
    level?: string;
  };
  alerts?: {
    count?: number;
    items?: Array<{
      severity?: string;
      message?: string;
      recommendation?: string;
      recommendations?: string[];
    }>;
  };
};

type HistoryRecord = {
  timestamp: string;
  particulate_matter?: { pm2_5_ugm3?: number };
  climate?: { temperature_c?: number; humidity_pct?: number };
  gas?: { co_ppm?: number };
};

type HistoryResponse = {
  records: HistoryRecord[];
};

type Mode = "realtime" | "seeded";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const REFRESH_SECONDS = Number(process.env.NEXT_PUBLIC_REFRESH_SECONDS ?? 15);
const STALE_MINUTES = Number(process.env.NEXT_PUBLIC_STALE_MINUTES ?? 3);

function numberOrDash(value?: number | null, suffix = ""): string {
  if (value == null || Number.isNaN(value)) return "-";
  return `${value.toFixed(1)}${suffix}`;
}

function aqiColor(aqi?: number): string {
  if (aqi === undefined) return "#64748b";
  if (aqi <= 50) return "#22c55e";
  if (aqi <= 100) return "#eab308";
  if (aqi <= 150) return "#f97316";
  if (aqi <= 200) return "#ef4444";
  return "#7c3aed";
}

function severityClassName(severity?: string): string {
  const normalized = (severity ?? "").toLowerCase();
  if (normalized.includes("high") || normalized.includes("danger")) return styles.severityHigh;
  if (normalized.includes("medium") || normalized.includes("warning")) return styles.severityMedium;
  return styles.severityLow;
}

function alertRecommendationText(item: { recommendation?: string; recommendations?: string[] }): string {
  if (item.recommendation) return item.recommendation;
  if (item.recommendations?.length) return item.recommendations.join(" · ");
  return "No recommendation";
}

function buildSeededHistory(points: number): HistoryRecord[] {
  return Array.from({ length: points }, (_, i) => {
    const minutesAgo = (points - i) * 5;
    const ts = new Date(Date.now() - minutesAgo * 60_000).toISOString();
    return {
      timestamp: ts,
      particulate_matter: { pm2_5_ugm3: 18 + Math.sin(i / 5) * 6 + (i % 4) },
      climate: { temperature_c: 30 + Math.sin(i / 8), humidity_pct: 56 + Math.cos(i / 10) * 4 },
      gas: { co_ppm: 8 + Math.sin(i / 6) * 3 },
    };
  });
}

function seededDashboard(): DashboardResponse {
  return {
    sensors: {
      particulate_matter: { pm1_0_ugm3: 11, pm2_5_ugm3: 22, pm10_ugm3: 34 },
      climate: { temperature_c: 30.8, humidity_pct: 58 },
      gas: { co_ppm: 10.5 },
      last_updated: new Date().toISOString(),
    },
    local_aqi: { aqi: 84, category: "Moderate" },
    comparison: { city_aqi: 72, global_avg_aqi: 79, local_rank_percentile: 58 },
    trends: { trend: "stable", predicted_pm2_5_1h: 24 },
    awareness: { score: 63.2, level: "Normal" },
    alerts: {
      count: 1,
      items: [
        {
          severity: "low",
          message: "Sensitive users may reduce prolonged outdoor activity.",
          recommendation: "Use mask if staying outdoor for long periods.",
        },
      ],
    },
  };
}

function AxisLineChart({
  title,
  values,
  timestamps,
  color,
  unit,
}: {
  title: string;
  values: number[];
  timestamps: string[];
  color: string;
  unit: string;
}) {
  const width = 560;
  const height = 300;
  const margin = { top: 14, right: 14, bottom: 36, left: 52 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const chartData = useMemo(
    () =>
      values
        .map((value, index) => ({ value, ts: timestamps[index] }))
        .filter((d) => Number.isFinite(d.value) && d.ts),
    [values, timestamps],
  );

  const { points, yTicks, xTicks, latest, minValue, maxValue } = useMemo(() => {
    if (!chartData.length) {
      return {
        points: "",
        yTicks: [] as Array<{ label: string; y: number; value: number }>,
        xTicks: [] as Array<{ label: string; x: number }>,
        latest: undefined as number | undefined,
        minValue: undefined as number | undefined,
        maxValue: undefined as number | undefined,
      };
    }

    const minY = Math.min(...chartData.map((d) => d.value));
    const maxY = Math.max(...chartData.map((d) => d.value));
    const yRange = maxY - minY || 1;
    const yPad = yRange * 0.1;
    const domainMin = Math.max(0, minY - yPad);
    const domainMax = maxY + yPad;
    const domainRange = domainMax - domainMin || 1;

    const pointText = chartData
      .map((d, i) => {
        const x = margin.left + (i / Math.max(chartData.length - 1, 1)) * plotW;
        const y = margin.top + (1 - (d.value - domainMin) / domainRange) * plotH;
        return `${x},${y}`;
      })
      .join(" ");

    const computedYTicks = Array.from({ length: 5 }, (_, i) => {
      const ratio = i / 4;
      const value = domainMax - ratio * domainRange;
      const y = margin.top + ratio * plotH;
      return { label: value.toFixed(1), y, value };
    });

    const xIdx = [0, Math.floor((chartData.length - 1) / 2), chartData.length - 1];
    const computedXTicks = xIdx.map((idx) => {
      const ts = new Date(chartData[idx].ts);
      const label = Number.isNaN(ts.getTime())
        ? "-"
        : ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const x = margin.left + (idx / Math.max(chartData.length - 1, 1)) * plotW;
      return { label, x };
    });

    return {
      points: pointText,
      yTicks: computedYTicks,
      xTicks: computedXTicks,
      latest: chartData[chartData.length - 1].value,
      minValue: minY,
      maxValue: maxY,
    };
  }, [chartData, margin.left, margin.top, plotH, plotW]);

  return (
    <section className={`${styles.card} ${styles.chartCard}`}>
      <div className={styles.chartHeader}>
        <h3>{title}</h3>
        <div className={styles.chartMeta}>
          <span>Min {numberOrDash(minValue)}</span>
          <span>Max {numberOrDash(maxValue)}</span>
          <span className={styles.chartBadge}>Live</span>
        </div>
      </div>
      {chartData.length ? (
        <>
          <svg
            className={styles.chart}
            viewBox={`0 0 ${width} ${height}`}
            role="img"
            aria-label={`${title} chart with x-axis time and y-axis values`}
          >
            {Array.from({ length: 4 }).map((_, i) => {
              const sectionY = margin.top + (i / 4) * plotH;
              return (
                <rect
                  key={`${title}-section-${i}`}
                  x={margin.left}
                  y={sectionY}
                  width={plotW}
                  height={plotH / 4}
                  className={i % 2 === 0 ? styles.sectionBand : styles.sectionBandAlt}
                />
              );
            })}

            <line className={styles.axisLine} x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} />
            <line
              className={styles.axisLine}
              x1={margin.left}
              y1={margin.top + plotH}
              x2={margin.left + plotW}
              y2={margin.top + plotH}
            />

            {yTicks.map((tick) => (
              <g key={`${title}-y-${tick.label}`}>
                <line className={styles.gridLine} x1={margin.left} y1={tick.y} x2={margin.left + plotW} y2={tick.y} />
                <text className={styles.axisTick} x={margin.left - 8} y={tick.y + 4} textAnchor="end">
                  {tick.label}
                </text>
              </g>
            ))}

            {xTicks.map((tick, idx) => (
              <g key={`${title}-x-${tick.label}-${idx}`}>
                <line className={styles.gridLineVertical} x1={tick.x} y1={margin.top} x2={tick.x} y2={margin.top + plotH} />
                <text className={styles.axisTick} x={tick.x} y={margin.top + plotH + 18} textAnchor="middle">
                  {tick.label}
                </text>
              </g>
            ))}

            <polyline fill="none" stroke={color} strokeWidth="2.6" points={points} />

            <text className={styles.axisLabel} x={16} y={margin.top + plotH / 2} transform={`rotate(-90 16 ${margin.top + plotH / 2})`}>
              Value ({unit})
            </text>
            <text className={styles.axisLabel} x={margin.left + plotW / 2} y={height - 6} textAnchor="middle">
              Time
            </text>
          </svg>
          <div className={styles.chartLegend}>
            <span>Y-axis: {unit}</span>
            <span>X-axis: Time</span>
            <span>Latest: {numberOrDash(latest, unit ? ` ${unit}` : "")}</span>
          </div>
        </>
      ) : (
        <p className={styles.empty}>No data</p>
      )}
    </section>
  );
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("realtime");
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    if (mode === "seeded") {
      setDashboard(seededDashboard());
      setHistory(buildSeededHistory(72));
      setLastRefresh(new Date());
      setLoading(false);
      return;
    }

    try {
      if (simulateFailure) {
        throw new Error("Simulated endpoint failure is active.");
      }
      const [dashRes, histRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/dashboard`, { cache: "no-store" }),
        fetch(`${API_BASE}/api/v1/history?limit=120`, { cache: "no-store" }),
      ]);
      if (!dashRes.ok || !histRes.ok) {
        throw new Error(`API error: dashboard=${dashRes.status}, history=${histRes.status}`);
      }
      const dashData = (await dashRes.json()) as DashboardResponse;
      const historyData = (await histRes.json()) as HistoryResponse;
      setDashboard(dashData);
      setHistory(historyData.records ?? []);
      setLastRefresh(new Date());
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [mode, simulateFailure]);

  useEffect(() => {
    void fetchData();
    const interval = window.setInterval(() => {
      void fetchData();
    }, REFRESH_SECONDS * 1000);
    return () => window.clearInterval(interval);
  }, [fetchData]);

  const latestTimestamp = dashboard?.sensors?.last_updated;
  const stale = useMemo(() => {
    if (!latestTimestamp) return false;
    const tsMs = new Date(latestTimestamp).getTime();
    if (Number.isNaN(tsMs)) return false;
    return Date.now() - tsMs > STALE_MINUTES * 60_000;
  }, [latestTimestamp]);

  const pm25Series = history.map((r) => r.particulate_matter?.pm2_5_ugm3 ?? 0);
  const tempSeries = history.map((r) => r.climate?.temperature_c ?? 0);
  const humiditySeries = history.map((r) => r.climate?.humidity_pct ?? 0);
  const coSeries = history.map((r) => r.gas?.co_ppm ?? 0);
  const cityAqi = dashboard?.comparison?.city_aqi ?? 0;
  const localAqi = dashboard?.local_aqi?.aqi ?? 0;
  const globalAqi = dashboard?.comparison?.global_avg_aqi ?? 0;

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <header className={styles.header}>
          <div>
            <h1>Smart Air Quality Dashboard</h1>
            <p>Auto refresh every {REFRESH_SECONDS}s | Timezone: {timezone}</p>
          </div>
          <div className={styles.controls}>
            <label>
              Mode
              <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
                <option value="realtime">Real-time</option>
                <option value="seeded">Seeded demo</option>
              </select>
            </label>
            <label className={styles.checkbox}>
              <input
                type="checkbox"
                checked={simulateFailure}
                onChange={(e) => setSimulateFailure(e.target.checked)}
                disabled={mode === "seeded"}
              />
              Simulate endpoint failure
            </label>
            <button onClick={() => void fetchData()} type="button">
              Refresh now
            </button>
          </div>
        </header>

        <section className={styles.quickStats}>
          <article className={styles.statCard}>
            <span>Local AQI</span>
            <strong>{localAqi || "-"}</strong>
          </article>
          <article className={styles.statCard}>
            <span>City AQI</span>
            <strong>{cityAqi || "-"}</strong>
          </article>
          <article className={styles.statCard}>
            <span>Global AQI</span>
            <strong>{globalAqi || "-"}</strong>
          </article>
          <article className={styles.statCard}>
            <span>Awareness</span>
            <strong>{numberOrDash(dashboard?.awareness?.score)}</strong>
          </article>
        </section>

        {loading && <p className={styles.state}>Loading dashboard...</p>}
        {error && <p className={styles.error}>Error: {error}</p>}
        {!loading && !error && !dashboard && <p className={styles.state}>No dashboard data</p>}

        {stale && <p className={styles.warning}>Stale data warning: no update for more than {STALE_MINUTES} minutes.</p>}

        {dashboard && (
          <>
            <section className={styles.grid}>
              <article className={`${styles.card} ${styles.cardAccentBlue}`}>
                <h3>Live Sensor Card</h3>
                <p>PM1.0: {numberOrDash(dashboard.sensors?.particulate_matter?.pm1_0_ugm3, " ug/m3")}</p>
                <p>PM2.5: {numberOrDash(dashboard.sensors?.particulate_matter?.pm2_5_ugm3, " ug/m3")}</p>
                <p>PM10: {numberOrDash(dashboard.sensors?.particulate_matter?.pm10_ugm3, " ug/m3")}</p>
                <p>Temp: {numberOrDash(dashboard.sensors?.climate?.temperature_c, " C")}</p>
                <p>Humidity: {numberOrDash(dashboard.sensors?.climate?.humidity_pct, " %")}</p>
                <p>CO: {numberOrDash(dashboard.sensors?.gas?.co_ppm, " ppm")}</p>
                <p className={styles.muted}>Last update: {latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "-"}</p>
              </article>

              <article className={`${styles.card} ${styles.cardAccentOrange}`}>
                <h3>AQI Card</h3>
                <p className={styles.aqiValue} style={{ color: aqiColor(dashboard.local_aqi?.aqi) }}>
                  {dashboard.local_aqi?.aqi ?? "-"}
                </p>
                <p>Category: {dashboard.local_aqi?.category ?? "-"}</p>
                <p className={styles.muted}>
                  Health message: {dashboard.local_aqi?.health_message ?? dashboard.local_aqi?.category ?? "Unknown condition"}
                </p>
              </article>

              <article className={`${styles.card} ${styles.cardAccentPurple}`}>
                <h3>Comparison Card</h3>
                <p>Local AQI: {localAqi}</p>
                <p>City AQI: {cityAqi}</p>
                <p>Global AQI: {globalAqi}</p>
                <p>
                  Rank percentile:{" "}
                  {numberOrDash(
                    dashboard.comparison?.local_rank_percentile ?? dashboard.comparison?.percentile_clean,
                    "%",
                  )}
                </p>
              </article>

              <article className={`${styles.card} ${styles.cardAccentTeal}`}>
                <h3>Trend Card</h3>
                <p>Trend (6/12/24h): {dashboard.trends?.trend ?? "-"}</p>
                <p>
                  Prediction (1h):{" "}
                  {numberOrDash(
                    dashboard.trends?.predicted_pm2_5_1h ?? dashboard.trends?.predicted_pm25_1h,
                    " ug/m3",
                  )}
                </p>
                <p className={styles.muted}>History records: {history.length}</p>
              </article>

              <article className={styles.card}>
                <h3>Awareness Score Card</h3>
                <p className={styles.score}>{numberOrDash(dashboard.awareness?.score)}</p>
                <span className={styles.badge}>{dashboard.awareness?.level ?? "Unknown"}</span>
              </article>

              <article className={`${styles.card} ${styles.fullWidthCard}`}>
                <h3>Alerts Panel</h3>
                {dashboard.alerts?.items?.length ? (
                  <ul className={styles.alertList}>
                    {dashboard.alerts.items.map((item, idx) => (
                      <li key={`${item.message ?? "alert"}-${idx}`}>
                        <strong className={severityClassName(item.severity)}>{item.severity ?? "unknown"}</strong>{" "}
                        {item.message ?? "No message"} — {alertRecommendationText(item)}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className={styles.empty}>No active alerts</p>
                )}
              </article>
            </section>

            <section className={styles.chartsGrid}>
              <AxisLineChart
                title="PM2.5 Time-Series"
                values={pm25Series}
                timestamps={history.map((r) => r.timestamp)}
                color="#f97316"
                unit="ug/m3"
              />
              <AxisLineChart
                title="Temperature Chart"
                values={tempSeries}
                timestamps={history.map((r) => r.timestamp)}
                color="#0ea5e9"
                unit="C"
              />
              <AxisLineChart
                title="Humidity Chart"
                values={humiditySeries}
                timestamps={history.map((r) => r.timestamp)}
                color="#14b8a6"
                unit="%"
              />
              <AxisLineChart
                title="CO Chart"
                values={coSeries}
                timestamps={history.map((r) => r.timestamp)}
                color="#ef4444"
                unit="ppm"
              />
              <article className={`${styles.card} ${styles.chartCard} ${styles.fullWidthCard}`}>
                <h3>AQI Bar Compare</h3>
                <div className={styles.barWrap}>
                  {[
                    { name: "Local", value: localAqi, color: "#6366f1" },
                    { name: "City", value: cityAqi, color: "#06b6d4" },
                    { name: "Global", value: globalAqi, color: "#84cc16" },
                  ].map((item) => (
                    <div key={item.name} className={styles.barItem}>
                      <p>{item.name}</p>
                      <div className={styles.barTrack}>
                        <div
                          className={styles.barFill}
                          style={{ width: `${Math.min(item.value, 300) / 3}%`, backgroundColor: item.color }}
                        />
                      </div>
                      <p>{item.value}</p>
                    </div>
                  ))}
                </div>
              </article>
            </section>
          </>
        )}

        <footer className={styles.footer}>
          <p>Last refreshed: {lastRefresh ? lastRefresh.toLocaleTimeString() : "-"}</p>
        </footer>
      </main>
    </div>
  );
}
