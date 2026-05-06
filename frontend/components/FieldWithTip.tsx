"use client";

import { useState } from "react";

export function FieldWithTip({
  label,
  tip,
  children,
}: {
  label: string;
  tip?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1">
        <label className="block text-sm text-gray-400">{label}</label>
        {tip && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              onBlur={() => setOpen(false)}
              className="w-4 h-4 rounded-full bg-gray-700 hover:bg-gray-600 text-gray-400 text-[10px] flex items-center justify-center leading-none transition-colors"
            >
              ?
            </button>
            {open && (
              <div className="absolute z-20 left-0 top-6 w-64 bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-300 shadow-xl">
                {tip}
              </div>
            )}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}
