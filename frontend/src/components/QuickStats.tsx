import { DashboardResponse } from "@/types/dashboard";
import { numberOrDash } from "@/lib/utils";
import { Cloud, Globe, MapPin, ShieldAlert } from "lucide-react";
import { InfoTooltip } from "./InfoTooltip";

interface QuickStatsProps {
  dashboard: DashboardResponse | null;
}

export function QuickStats({ dashboard }: QuickStatsProps) {
  const localAqi = dashboard?.local_aqi?.aqi ?? 0;
  const cityAqi = dashboard?.comparison?.city_aqi ?? 0;
  const globalAqi = dashboard?.comparison?.global_avg_aqi ?? 0;
  const awarenessScore = dashboard?.awareness?.score;

  const stats = [
    {
      label: "Local AQI",
      value: localAqi || "-",
      icon: MapPin,
      color: "text-red-600",
      bg: "bg-red-50",
      info: "Air Quality Index measured by your local hardware sensor based on US EPA standards.",
      subtext: "Live updates",
    },
    {
      label: "City AQI",
      value: cityAqi || "-",
      icon: Cloud,
      color: "text-gray-900",
      bg: "bg-gray-100",
      info: "Average Air Quality Index for the city from external API sources.",
      subtext: "Updates every 15m",
    },
    {
      label: "Global AQI",
      value: globalAqi || "-",
      icon: Globe,
      color: "text-gray-600",
      bg: "bg-gray-50",
      info: "Average Air Quality Index from a sample of major cities worldwide.",
      subtext: "Updates every 15m",
    },
    {
      label: "Awareness",
      value: numberOrDash(awarenessScore),
      icon: ShieldAlert,
      color: "text-red-700",
      bg: "bg-red-100",
      info: "A calculated score (0-100) indicating how critical the local air quality is compared to global standards.",
      subtext: "Live updates",
    },
  ];

  return (
    <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-white border-2 border-gray-900/20 rounded-xl p-5 flex items-center gap-4 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300"
        >
          <div className={`p-3 rounded-lg ${stat.bg} ${stat.color}`}>
            <stat.icon className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center">
              {stat.label}
              <InfoTooltip text={stat.info} />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-0.5">
              {stat.value}
            </p>
            {stat.subtext && (
              <p className="text-[10px] text-gray-400 mt-0.5 font-medium">
                {stat.subtext}
              </p>
            )}
          </div>
        </div>
      ))}
    </section>
  );
}
