import { DashboardResponse } from "@/types/dashboard";
import { aqiColor, numberOrDash } from "@/lib/utils";
import { InfoTooltip } from "./InfoTooltip";

interface OverviewProps {
  dashboard: DashboardResponse;
}

export function Overview({ dashboard }: OverviewProps) {
  const latestTimestamp = dashboard.sensors?.last_updated;
  const localAqi = dashboard.local_aqi?.aqi ?? 0;
  const cityAqi = dashboard.comparison?.city_aqi ?? 0;
  const globalAqi = dashboard.comparison?.global_avg_aqi ?? 0;

  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Live Sensor Card */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          Live Sensor
          <InfoTooltip text="Real-time readings directly from the local hardware sensors (PM, Temperature, Humidity, CO)." />
        </h3>
        <div className="space-y-3 text-sm text-gray-600 flex-grow">
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">PM1.0:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.particulate_matter?.pm1_0_ugm3, " µg/m³")}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">PM2.5:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.particulate_matter?.pm2_5_ugm3, " µg/m³")}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">PM10:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.particulate_matter?.pm10_ugm3, " µg/m³")}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">Temp:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.climate?.temperature_c, " °C")}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">Humidity:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.climate?.humidity_pct, " %")}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-gray-500">CO:</span>
            <span className="font-medium text-gray-900">{numberOrDash(dashboard.sensors?.gas?.co_ppm, " ppm")}</span>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-6 pt-4 border-t border-gray-100">
          Last update: {latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "-"}
        </p>
      </article>

      {/* Local AQI Card */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          Local AQI
          <InfoTooltip text="Calculated Air Quality Index based on US EPA standards, primarily driven by PM2.5 concentration." />
        </h3>
        <div className="flex-grow flex flex-col items-center justify-center py-6">
          <p
            className="text-7xl font-bold tracking-tighter mb-2"
            style={{ color: aqiColor(dashboard.local_aqi?.aqi) }}
          >
            {dashboard.local_aqi?.aqi ?? "-"}
          </p>
          <p className="text-lg font-medium text-gray-800">
            {dashboard.local_aqi?.category ?? "-"}
          </p>
        </div>
        <p className="text-sm text-gray-500 text-center mt-auto pt-4 border-t border-gray-100">
          {dashboard.local_aqi?.health_message ?? dashboard.local_aqi?.category ?? "Unknown condition"}
        </p>
      </article>

      {/* AQI Bar Compare */}
      <article className="bg-white border-2 border-gray-900/20 rounded-xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.2)] hover:-translate-y-1 transition-all duration-300 flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4 mb-5 flex items-center">
          AQI Comparison
          <InfoTooltip text="Visual comparison of your local air quality against the city average and global average." />
        </h3>
        <div className="space-y-6 flex-grow py-2">
          {[
            { name: "Local", value: localAqi, color: "bg-red-600" },
            { name: "City", value: cityAqi, color: "bg-gray-900" },
            { name: "Global", value: globalAqi, color: "bg-gray-300" },
          ].map((item) => (
            <div key={item.name} className="flex items-center gap-4 text-sm">
              <p className="w-16 font-medium text-gray-500">{item.name}</p>
              <div className="flex-1 h-3 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className={`h-full rounded-full ${item.color} transition-all duration-500`}
                  style={{ width: `${Math.min(item.value, 300) / 3}%` }}
                />
              </div>
              <p className="w-10 text-right font-semibold text-gray-900">{item.value}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
