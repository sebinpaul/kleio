"use client";

import React from "react";
import { Chip } from "@/components/ui/chip";
import { SUPPORTED_LANGUAGES } from "@/lib/enums";
import FieldLabel from "@/components/FieldLabel";

type LanguageMultiSelectProps = {
  id: string;
  label: string;
  tooltip: string;
  selected: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
};

export default function LanguageMultiSelect({
  id,
  label,
  tooltip,
  selected,
  onChange,
  disabled = false,
}: LanguageMultiSelectProps) {
  const toggleLanguage = (code: string) => {
    if (disabled) return;
    if (selected.includes(code)) {
      onChange(selected.filter((item) => item !== code));
    } else {
      onChange([...selected, code]);
    }
  };

  return (
    <div className="space-y-2">
      <FieldLabel htmlFor={id} label={label} tooltip={tooltip} />
      <div
        id={id}
        className="grid grid-cols-3 sm:grid-cols-5 gap-1.5 rounded-lg border border-slate-200 bg-slate-50 p-2"
      >
        {SUPPORTED_LANGUAGES.map((language) => {
          const isSelected = selected.includes(language.code);
          return (
            <button
              key={language.code}
              type="button"
              disabled={disabled}
              onClick={() => toggleLanguage(language.code)}
              className="disabled:opacity-60 text-left"
            >
              <Chip
                className={`w-full justify-center text-xs px-2 py-1 ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-600 text-white"
                    : "border-slate-300 bg-white text-slate-700 hover:border-indigo-300"
                }`}
              >
                {language.label}
              </Chip>
            </button>
          );
        })}
      </div>
    </div>
  );
}
