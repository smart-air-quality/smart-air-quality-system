import { Info } from "lucide-react";

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  return (
    <div className="group relative inline-flex items-center justify-center ml-1.5 align-middle">
      <Info className="w-4 h-4 text-gray-400 hover:text-red-600 cursor-help transition-colors" />
      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover:block w-64 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl z-50 text-center font-medium tracking-wide leading-relaxed pointer-events-none">
        {text}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
      </div>
    </div>
  );
}
