import { useState, useMemo } from "react";
import { DashboardResponse, HistoryRecord } from "@/types/dashboard";
import {
  alertRecommendationText,
  numberOrDash,
  severityColorClass,
} from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Activity,
} from "lucide-react";
import { InfoTooltip } from "./InfoTooltip";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface AnalysisProps {
  dashboard: DashboardResponse;
  history: HistoryRecord[];
}

export function Analysis({ dashboard, history }: AnalysisProps) {
  const [showCitiesList, setShowCitiesList] = useState(false);
  const [showTrendInfo, setShowTrendInfo] = useState(false);
  const [showAwarenessInfo, setShowAwarenessInfo] = useState(false);

  const localAqi = dashboard.local_aqi?.aqi ?? 0;
  const cityAqi = dashboard.comparison?.city_aqi ?? 0;
  const globalAqi = dashboard.comparison?.global_avg_aqi ?? 0;

  const trendChartData = useMemo(() => {
    const raw = history
      .map((r) => ({
        ts: new Date(r.timestamp).getTime(),
        pm25: r.particulate_matter?.pm2_5_ugm3,
      }))
      .filter((d) => d.pm25 !== undefined && !Number.isNaN(d.ts))
      .sort((a, b) => a.ts - b.ts);

    if (raw.length === 0) return [];

    const latestRecordTs = raw[raw.length - 1].ts;
    const sixHoursAgo = latestRecordTs - 6 * 60 * 60 * 1000;
    const filtered = raw.filter((d) => d.ts >= sixHoursAgo);

    if (filtered.length === 0) return [];

    const latestTs = filtered[filtered.length - 1].ts;
    const lastVal =
      dashboard.trends?.current_pm25 ?? filtered[filtered.length - 1].pm25!;
    const slopePerHour = dashboard.trends?.slope_per_hour ?? 0;
    const slopePerMs = slopePerHour / (60 * 60 * 1000);

    const chartData = filtered.map((d) => {
      const trendVal = lastVal + slopePerMs * (d.ts - latestTs);
      return {
        time: new Date(d.ts).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        Actual: d.pm25,
        Trend: Math.max(0, Number(trendVal.toFixed(1))),
      };
    });

    const futureTs = latestTs + 60 * 60 * 1000; // +1 hour
    const futureTrendVal = lastVal + slopePerHour;
    chartData.push({
      time:
        new Date(futureTs).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }) + " (Pred)",
      Actual: undefined,
      Trend: Math.max(0, Number(futureTrendVal.toFixed(1))),
    });

    return chartData;
  }, [history, dashboard.trends]);

  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Comparison Details */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          Comparison Metrics
          <InfoTooltip text="Detailed breakdown of how your local air quality compares to external sources and global samples." />
        </h3>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">Local AQI:</span>
            <span className="font-medium text-gray-900">{localAqi}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">City AQI:</span>
            <span className="font-medium text-gray-900">{cityAqi}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">Global AQI:</span>
            <span className="font-medium text-gray-900">{globalAqi}</span>
          </div>
          <div className="flex justify-between">
            <div className="font-medium text-gray-500 flex items-center">
              Percentile:
              <InfoTooltip text="Percentage of sampled global cities that have WORSE air quality than your local sensor." />
            </div>
            <span className="font-medium text-gray-900">
              {numberOrDash(
                dashboard.comparison?.local_rank_percentile ??
                  dashboard.comparison?.percentile_clean,
                "%",
              )}
            </span>
          </div>
        </div>
        <div className="mt-5 bg-gray-50 border-2 border-gray-900/20 text-gray-700 text-sm p-3.5 rounded-lg leading-relaxed">
          <span className="font-semibold block mb-1 text-gray-900">
            Analysis:
          </span>
          {dashboard.comparison?.summary ?? "No summary available"}
        </div>

        <div className="mt-auto pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowCitiesList(!showCitiesList)}
            className="flex items-center justify-between w-full text-sm text-gray-500 hover:text-gray-900 font-medium transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Activity className="w-4 h-4" /> View sample cities
            </span>
            {showCitiesList ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {showCitiesList && (
            <div className="mt-3 max-h-48 overflow-y-auto bg-gray-50 border-2 border-gray-900/20 rounded-lg p-2 animate-in slide-in-from-top-2 fade-in duration-200 custom-scrollbar">
              {dashboard.global_samples &&
              dashboard.global_samples.length > 0 ? (
                <ul className="space-y-1">
                  {dashboard.global_samples.map((sample, idx) => (
                    <li
                      key={idx}
                      className="flex justify-between items-center p-2 hover:bg-gray-100 rounded-md text-sm transition-colors"
                    >
                      <span
                        className="text-gray-700 truncate mr-2"
                        title={sample.city}
                      >
                        {sample.city}
                      </span>
                      <span className="font-semibold text-gray-900 shrink-0">
                        AQI: {sample.aqi}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-3 text-center text-sm text-gray-500">
                  No sample cities available.
                </div>
              )}
            </div>
          )}
        </div>
      </article>

      {/* Trend Analysis */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          Trend Analysis
          <InfoTooltip text="Predicts PM2.5 levels for the next hour based on the last 6 hours of data using linear regression." />
        </h3>
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex justify-between items-center">
            <span className="font-medium text-gray-500">Trend (6h):</span>
            <span className="capitalize px-3 py-1 bg-gray-100 text-gray-800 rounded-md font-medium">
              {dashboard.trends?.trend ?? "-"}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-medium text-gray-500">Prediction (1h):</span>
            <span className="font-semibold text-lg text-gray-900">
              {numberOrDash(
                dashboard.trends?.predicted_pm2_5_1h ??
                  dashboard.trends?.predicted_pm25_1h,
                " µg/m³",
              )}
            </span>
          </div>
        </div>

        {trendChartData.length > 0 && (
          <div className="h-32 w-full mt-4 -ml-4">
            <ResponsiveContainer
              width="100%"
              height="100%"
              minWidth={0}
              minHeight={0}
            >
              <LineChart data={trendChartData}>
                <XAxis dataKey="time" hide />
                <YAxis domain={["auto", "auto"]} hide />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    fontSize: "12px",
                  }}
                  itemStyle={{ color: "#111827", fontWeight: 500 }}
                  labelStyle={{ display: "none" }}
                  formatter={(
                    value:
                      | number
                      | string
                      | ReadonlyArray<number | string>
                      | undefined,
                    name: number | string | undefined,
                  ) => [`${value ?? 0} µg/m³`, String(name ?? "")]}
                />
                <Line
                  type="monotone"
                  dataKey="Actual"
                  stroke="#94a3b8"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="Trend"
                  stroke="#ef4444"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="mt-auto pt-4 border-t border-gray-100 flex flex-col justify-end">
          <button
            onClick={() => setShowTrendInfo(!showTrendInfo)}
            className="flex items-center justify-between w-full text-sm text-gray-500 hover:text-gray-900 font-medium transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Activity className="w-4 h-4" /> View details
            </span>
            {showTrendInfo ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {showTrendInfo && (
            <div className="mt-3 bg-gray-50 border-2 border-gray-900/20 text-gray-700 text-sm p-3.5 rounded-lg leading-relaxed animate-in slide-in-from-top-2 fade-in duration-200">
              <span className="font-semibold block mb-1 text-gray-900">
                Analysis:
              </span>
              {dashboard.trends?.trend?.toLowerCase() === "worsening"
                ? "PM2.5 levels have been consistently rising over the past 6 hours, leading to a higher predicted value."
                : dashboard.trends?.trend?.toLowerCase() === "improving"
                  ? "PM2.5 levels have been decreasing over the past 6 hours, indicating better air quality ahead."
                  : "PM2.5 levels have remained relatively stable over the past 6 hours, so no major changes are expected."}
            </div>
          )}
          <p className="text-xs text-gray-400 mt-3 text-right">
            Based on {history.length} recent records
          </p>
        </div>
      </article>

      {/* Awareness Score */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          Awareness Score
          <InfoTooltip text="A calculated score (0-100) combining local AQI severity and your global ranking percentile." />
        </h3>
        <div className="flex-grow flex flex-col items-center justify-center py-2">
          <p className="text-6xl font-bold text-gray-900 mb-4">
            {numberOrDash(dashboard.awareness?.score)}
          </p>
          <span className="px-4 py-1.5 bg-red-50 text-red-700 border border-red-100 rounded-full text-sm font-semibold tracking-wide mb-4">
            {dashboard.awareness?.level ?? "Unknown"}
          </span>
        </div>
        <div className="mt-auto pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowAwarenessInfo(!showAwarenessInfo)}
            className="flex items-center justify-between w-full text-sm text-gray-500 hover:text-gray-900 font-medium transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Activity className="w-4 h-4" /> View details
            </span>
            {showAwarenessInfo ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {showAwarenessInfo && (
            <div className="mt-3 bg-gray-50 border-2 border-gray-900/20 text-gray-700 text-sm p-3.5 rounded-lg leading-relaxed animate-in slide-in-from-top-2 fade-in duration-200">
              <span className="font-semibold block mb-1 text-gray-900">
                Analysis:
              </span>
              {dashboard.awareness?.level?.toLowerCase() === "critical"
                ? "Your local air quality is significantly worse than the global baseline, requiring immediate attention."
                : dashboard.awareness?.level?.toLowerCase() === "elevated"
                  ? "Your local air quality is worse than average compared to global cities."
                  : "Your local air quality is within a normal range compared to global cities."}
            </div>
          )}
        </div>
      </article>

      {/* Alerts Panel */}
      <article className="lg:col-span-3 bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-gray-900" />
          Active Alerts
          <InfoTooltip text="Automated warnings generated when pollutant levels exceed safe thresholds or when trends worsen rapidly." />
        </h3>
        {dashboard.alerts?.items?.length ? (
          <ul className="space-y-3">
            {dashboard.alerts.items.map((item, idx) => (
              <li
                key={`${item.message ?? "alert"}-${idx}`}
                className="flex flex-col sm:flex-row sm:items-start gap-3 p-4 bg-gray-50 border border-gray-100 rounded-lg"
              >
                <span
                  className={`inline-flex items-center justify-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider whitespace-nowrap border ${severityColorClass(
                    item.severity,
                  )}`}
                >
                  {item.severity ?? "unknown"}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 mb-1">
                    {item.message ?? "No message"}
                  </p>
                  <p className="text-sm text-gray-600">
                    {alertRecommendationText(item)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-gray-400">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-3 opacity-50" />
            <p>No active alerts at this time.</p>
          </div>
        )}
      </article>
    </section>
  );
}
