"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { DashboardResponse, HistoryRecord, HistoryResponse, Tab } from "@/types/dashboard";
import { Navbar } from "@/components/Navbar";
import { QuickStats } from "@/components/QuickStats";
import { Overview } from "@/components/Overview";
import { Analysis } from "@/components/Analysis";
import { Charts } from "@/components/Charts";
import { AlertTriangle, Info } from "lucide-react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const REFRESH_SECONDS = Number(process.env.NEXT_PUBLIC_REFRESH_SECONDS ?? 15);
const STALE_MINUTES = Number(process.env.NEXT_PUBLIC_STALE_MINUTES ?? 3);

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

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
  }, [simulateFailure]);

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

  return (
    <div className="min-h-screen bg-[#fafafa] text-gray-900 font-sans selection:bg-red-100 selection:text-red-900">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRefresh={() => void fetchData()}
        refreshSeconds={REFRESH_SECONDS}
        isRefreshing={loading}
        isStale={stale}
      />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <QuickStats dashboard={dashboard} />

        {/* Status Messages */}
        <div className="mb-8 space-y-3">
          {loading && !dashboard && (
            <div className="flex items-center gap-2 px-4 py-3 bg-red-50 text-red-800 border border-red-200 rounded-xl text-sm shadow-sm">
              <Info className="w-4 h-4" /> Loading dashboard data...
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 bg-red-50 text-red-800 border border-red-200 rounded-xl text-sm shadow-sm">
              <AlertTriangle className="w-4 h-4" /> Error: {error}
            </div>
          )}
          {!loading && !error && !dashboard && (
            <div className="flex items-center gap-2 px-4 py-3 bg-gray-100 text-gray-600 border-2 border-gray-900/20 rounded-xl text-sm shadow-sm">
              <Info className="w-4 h-4" /> No dashboard data available.
            </div>
          )}
        </div>

        {dashboard && (
          <div className="flex flex-col items-center mb-8 lg:hidden">
            {/* Mobile/Tablet Pill Tab Navigation */}
            <nav className="flex p-1 space-x-1 bg-gray-100/80 border-2 border-gray-900/20 rounded-xl shadow-sm overflow-x-auto max-w-full">
              {[
                { id: "overview", label: "Overview" },
                { id: "analysis", label: "Analysis & Alerts" },
                { id: "charts", label: "Historical Charts" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as Tab)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 whitespace-nowrap ${
                    activeTab === tab.id
                      ? "bg-white text-red-600 shadow-sm border-2 border-gray-900/20"
                      : "text-gray-500 hover:text-gray-800 hover:bg-gray-200/50 border border-transparent"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        )}

        {dashboard && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
            {activeTab === "overview" && <Overview dashboard={dashboard} />}
            {activeTab === "analysis" && <Analysis dashboard={dashboard} history={history} />}
            {activeTab === "charts" && <Charts history={history} />}
          </div>
        )}

        <footer className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-16 pt-8 border-t-2 border-gray-900/20">
          <div className="flex flex-wrap justify-center items-center gap-x-4 gap-y-2 bg-white px-5 py-3 rounded-xl border-2 border-gray-900/20 shadow-sm text-sm font-medium text-gray-600">
            <div className="flex items-center gap-2">
              <span>Last refreshed: <strong className="text-gray-900">{lastRefresh ? lastRefresh.toLocaleTimeString() : "-"}</strong></span>
            </div>
            <span className="hidden sm:inline text-gray-300">|</span>
            <div className="flex items-center gap-2">
              <span>Timezone: <strong className="text-gray-900">{Intl.DateTimeFormat().resolvedOptions().timeZone}</strong></span>
            </div>
          </div>
          
          <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer hover:text-gray-700 transition-colors bg-white px-4 py-3 rounded-xl border-2 border-gray-900/20 shadow-sm font-medium">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-gray-300 text-red-600 focus:ring-red-600"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
            />
            Simulate API Failure
          </label>
        </footer>
      </main>
    </div>
  );
}
