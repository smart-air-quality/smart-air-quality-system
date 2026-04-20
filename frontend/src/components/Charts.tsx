import { HistoryRecord } from "@/types/dashboard";
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useMemo, useState } from "react";
import { numberOrDash } from "@/lib/utils";
import { InfoTooltip } from "./InfoTooltip";
import { History, ChevronDown, ChevronUp, Activity } from "lucide-react";

interface ChartProps {
  title: string;
  data: { ts: string; value: number }[];
  color: string;
  unit: string;
  info: string;
  description: string;
}

function MetricChart({ title, data, color, unit, info, description }: ChartProps) {
  const [showSummary, setShowSummary] = useState(false);

  const { min, max, latest, avg } = useMemo(() => {
    if (!data.length) return { min: null, max: null, latest: null, avg: null };
    const values = data.map((d) => d.value);
    const sum = values.reduce((a, b) => a + b, 0);
    return {
      min: Math.min(...values),
      max: Math.max(...values),
      latest: values[values.length - 1],
      avg: sum / values.length,
    };
  }, [data]);

  const formattedData = useMemo(() => {
    return data.map((d) => {
      const date = new Date(d.ts);
      return {
        ...d,
        time: Number.isNaN(date.getTime())
          ? "-"
          : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        fullDate: Number.isNaN(date.getTime()) ? "-" : date.toLocaleString(),
      };
    });
  }, [data]);

  return (
    <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col h-[480px]">
      <div className="mb-6 border-b border-gray-100 pb-5">
        <div className="flex justify-between items-start mb-2 gap-3">
          <div className="min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center flex-wrap gap-x-1">
              {title}
              <InfoTooltip text={info} />
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500 font-medium shrink-0">
            <span>Min: {numberOrDash(min)}</span>
            <span>Max: {numberOrDash(max)}</span>
            <span className="bg-gray-100 px-2 py-1 rounded-md text-gray-800 font-semibold">
              Live: {numberOrDash(latest)} {unit}
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowSummary(!showSummary)}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 font-medium transition-colors mt-1"
        >
          <Activity className="w-4 h-4" />
          {showSummary ? "Hide details" : "View details"}
          {showSummary ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
        </button>

        {showSummary && (
          <div className="mt-4 p-4 bg-gray-50 border-2 border-gray-900/20 rounded-lg text-sm text-gray-700 leading-relaxed animate-in slide-in-from-top-2 fade-in duration-200">
            <span className="font-semibold block mb-2 text-gray-900">Analysis:</span>
            {description}
            <div className="mt-3 pt-3 border-t border-gray-900/20 grid grid-cols-2 gap-4 text-xs">
              <div>
                <strong className="text-gray-900">Average:</strong> {numberOrDash(avg)} {unit}
              </div>
              <div>
                <strong className="text-gray-900">Status:</strong>{" "}
                {latest !== null && avg !== null
                  ? latest > avg
                    ? "Above Average"
                    : "Below Average"
                  : "-"}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grow w-full h-full min-h-0">
        {formattedData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <RechartsLineChart data={formattedData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#9ca3af"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                minTickGap={30}
              />
              <YAxis
                stroke="#9ca3af"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `${val}`}
                domain={["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                  fontSize: "14px",
                }}
                itemStyle={{ color: "#111827", fontWeight: 500 }}
                labelStyle={{ color: "#6b7280", marginBottom: "4px" }}
                labelFormatter={(_label, payload) => {
                  if (payload && payload.length > 0) {
                    return payload[0].payload.fullDate;
                  }
                  return _label;
                }}
                formatter={(value: number | string | ReadonlyArray<number | string> | undefined) => [
                  `${Number(value ?? 0).toFixed(1)} ${unit}`,
                  title,
                ]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, fill: color, stroke: "#fff", strokeWidth: 2 }}
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm italic">
            No data available
          </div>
        )}
      </div>
    </article>
  );
}

interface ChartsProps {
  history: HistoryRecord[];
}

export function Charts({ history }: ChartsProps) {
  const timestamps = history.map((h) => new Date(h.timestamp).getTime()).filter((t) => !Number.isNaN(t));
  const minTs = timestamps.length ? Math.min(...timestamps) : null;
  const maxTs = timestamps.length ? Math.max(...timestamps) : null;

  const startTimeStr = minTs ? new Date(minTs).toLocaleString() : "-";
  const endTimeStr = maxTs ? new Date(maxTs).toLocaleString() : "-";

  const pm25Data = history
    .map((r) => ({ ts: r.timestamp, value: r.particulate_matter?.pm2_5_ugm3 ?? 0 }))
    .filter((d) => Number.isFinite(d.value));

  const tempData = history
    .map((r) => ({ ts: r.timestamp, value: r.climate?.temperature_c ?? 0 }))
    .filter((d) => Number.isFinite(d.value));

  const humidityData = history
    .map((r) => ({ ts: r.timestamp, value: r.climate?.humidity_pct ?? 0 }))
    .filter((d) => Number.isFinite(d.value));

  const coData = history
    .map((r) => ({ ts: r.timestamp, value: r.gas?.co_ppm ?? 0 }))
    .filter((d) => Number.isFinite(d.value));

  return (
    <div className="space-y-6">
      <div className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] flex items-start gap-4">
        <div className="p-2.5 bg-gray-100 text-gray-700 rounded-lg shrink-0 mt-1">
          <History className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-1">Historical Data Overview</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Displaying <strong>{history.length}</strong> records from{" "}
            <strong className="text-gray-900">{startTimeStr}</strong> to{" "}
            <strong className="text-gray-900">{endTimeStr}</strong>. Each chart supports{" "}
            <strong className="text-gray-900">View details</strong> for a short analysis, the historical average, and
            whether the latest reading is above or below that average — matching the interactive historical charts
            described in the project scope.
          </p>
        </div>
      </div>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricChart
          title="PM2.5 Time-Series"
          data={pm25Data}
          color="#374151"
          unit="µg/m³"
          info="Historical PM2.5 particulate matter concentration over time."
          description="Tracks fine particulate matter (PM2.5). Spikes often indicate worsening air pollution from traffic, burning, or atmospheric conditions."
        />
        <MetricChart
          title="Temperature"
          data={tempData}
          color="#0284c7"
          unit="°C"
          info="Historical ambient temperature readings from the local sensor."
          description="Monitors ambient temperature changes. Noticeable patterns usually follow the time of day (cooler at night, hotter in the afternoon)."
        />
        <MetricChart
          title="Humidity"
          data={humidityData}
          color="#0d9488"
          unit="%"
          info="Historical relative humidity readings."
          description="Shows relative humidity levels. High humidity combined with high PM2.5 can make the air feel heavier and more polluted."
        />
        <MetricChart
          title="CO Level"
          data={coData}
          color="#6b7280"
          unit="ppm"
          info="Historical Carbon Monoxide gas concentration."
          description="Records Carbon Monoxide gas levels. Elevated levels are typically linked to vehicle emissions during rush hours."
        />
      </section>
    </div>
  );
}
