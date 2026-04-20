import { Tab } from "@/types/dashboard";
import { MapPin, Wind, RefreshCw } from "lucide-react";

/** Fixed demo / deployment context shown in the UI (city + WAQI / weather reference). */
const DETECTED_CITY = "Bangkok";
const DETECTED_LAT = 13.7563;
const DETECTED_LON = 100.5018;

function formatLatLon(lat: number, lon: number): string {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(4)}°${ns}, ${Math.abs(lon).toFixed(4)}°${ew}`;
}

interface NavbarProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  onRefresh: () => void;
  refreshSeconds: number;
  isRefreshing?: boolean;
  isStale?: boolean;
}

export function Navbar({
  activeTab,
  setActiveTab,
  onRefresh,
  refreshSeconds,
  isRefreshing,
  isStale,
}: NavbarProps) {
  const coords = formatLatLon(DETECTED_LAT, DETECTED_LON);

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b-2 border-gray-900/20 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 min-h-16 py-2 flex items-center justify-between gap-4">
        {/* Left: Logo & Title */}
        <div className="flex items-center gap-3 shrink-0 min-w-0">
          <div className="bg-red-600 p-1.5 rounded-lg shadow-md shrink-0">
            <Wind className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-bold tracking-tight text-gray-900 leading-tight">
              <span className="hidden sm:inline">Smart Air Quality</span>
              <span className="sm:hidden">Air Quality</span>
            </h1>
            <p
              className="mt-0.5 flex items-start gap-1 text-xs text-gray-500 font-medium leading-snug"
              title={`location: ${DETECTED_CITY} (${coords})`}
            >
              <MapPin
                className="w-3.5 h-3.5 shrink-0 mt-0.5 text-gray-400"
                aria-hidden
              />
              <span className="wrap-break-word">
                <span className="text-gray-600">Location: </span>
                <strong className="text-gray-800">{DETECTED_CITY}</strong>
                <span className="text-gray-600"> · </span>
                <span className="tabular-nums text-gray-700">{coords}</span>
              </span>
            </p>
          </div>
        </div>

        {/* Center: Tabs (Desktop) */}
        <nav className="hidden md:flex p-1 space-x-1 bg-gray-100/80 border-2 border-gray-900/20 rounded-xl">
          {[
            { id: "overview", label: "Overview" },
            { id: "analysis", label: "Analysis & Alerts" },
            { id: "charts", label: "Historical Charts" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-white text-red-600 shadow-sm border-2 border-gray-900/20"
                  : "text-gray-500 hover:text-gray-800 hover:bg-gray-200/50 border border-transparent"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-3 shrink-0">
          {isStale ? (
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 text-xs font-semibold border border-gray-200/80"
              title="No updates received from hardware sensors for over 3 minutes."
            >
              <span className="relative flex h-2 w-2">
                <span className="relative inline-flex rounded-full h-2 w-2 bg-gray-400"></span>
              </span>
              <span className="hidden sm:inline">Sensor Offline</span>
              <span className="sm:hidden">Offline</span>
            </div>
          ) : (
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 text-red-700 text-xs font-semibold border border-red-200/50"
              title={`Auto-refreshes every ${refreshSeconds}s`}
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              </span>
              <span className="hidden sm:inline">
                Live • Refresh {refreshSeconds}s
              </span>
              <span className="sm:hidden">Live</span>
            </div>
          )}

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 bg-white border-2 border-gray-900/20 hover:bg-gray-50 text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
            title="Refresh data now"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? "animate-spin text-red-600" : ""}`}
            />
            <span className="hidden sm:inline">
              {isRefreshing ? "Refreshing..." : "Refresh"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
