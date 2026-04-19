import { Tab } from "@/types/dashboard";
import { Wind, RefreshCw } from "lucide-react";

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
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b-2 border-gray-900/20 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Left: Logo & Title */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="bg-red-600 p-1.5 rounded-lg shadow-md">
            <Wind className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-bold tracking-tight text-gray-900 hidden sm:block">
            Smart Air Quality
          </h1>
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
              <span className="hidden sm:inline">
                Sensor Offline
              </span>
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
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-red-600" : ""}`} />
            <span className="hidden sm:inline">{isRefreshing ? "Refreshing..." : "Refresh"}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
