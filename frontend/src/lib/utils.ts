import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function numberOrDash(value?: number | null, suffix = ""): string {
  if (value == null || Number.isNaN(value)) return "-";
  return `${value.toFixed(1)}${suffix}`;
}

export function aqiColor(aqi?: number): string {
  if (aqi === undefined) return "#6b7280"; // gray-500
  if (aqi <= 50) return "#10b981"; // emerald-500
  if (aqi <= 100) return "#f59e0b"; // amber-500
  if (aqi <= 150) return "#f97316"; // orange-500
  if (aqi <= 200) return "#ef4444"; // red-500
  return "#8b5cf6"; // violet-500
}

export function severityColorClass(severity?: string): string {
  const normalized = (severity ?? "").toLowerCase();
  if (normalized.includes("high") || normalized.includes("danger")) {
    return "bg-red-50 text-red-700 border-red-200";
  }
  if (normalized.includes("medium") || normalized.includes("warning")) {
    return "bg-amber-50 text-amber-700 border-amber-200";
  }
  return "bg-emerald-50 text-emerald-700 border-emerald-200";
}

export function alertRecommendationText(item: { recommendation?: string; recommendations?: string[] }): string {
  if (item.recommendation) return item.recommendation;
  if (item.recommendations?.length) return item.recommendations.join(" · ");
  return "No recommendation";
}
