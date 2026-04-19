export type DashboardResponse = {
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
    local_rank_percentile?: number;
    percentile_clean?: number;
    summary?: string;
  };
  global_samples?: Array<{
    city: string;
    aqi: number;
    dominant_pollutant?: string;
    pm2_5?: number;
    pm10?: number;
    co?: number;
    temperature?: number;
    humidity?: number;
    source?: string;
  }>;
  trends?: {
    trend?: string;
    predicted_pm2_5_1h?: number;
    predicted_pm25_1h?: number;
    current_pm25?: number;
    slope_per_hour?: number;
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

export type HistoryRecord = {
  timestamp: string;
  particulate_matter?: { pm2_5_ugm3?: number };
  climate?: { temperature_c?: number; humidity_pct?: number };
  gas?: { co_ppm?: number };
};

export type HistoryResponse = {
  records: HistoryRecord[];
};

export type Tab = "overview" | "analysis" | "charts";
