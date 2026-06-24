"use client";

import React, { useState, KeyboardEvent } from "react";
import { Input } from "@/components/ui/input";
import { Chip } from "@/components/ui/chip";
import { cn } from "@/lib/utils";

type ChipInputProps = {
  id?: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  normalize?: (value: string) => string;
};

export default function ChipInput({
  id,
  values,
  onChange,
  placeholder = "Type and press Enter",
  disabled = false,
  className,
  normalize = (value) => value.trim(),
}: ChipInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addValue = (raw: string) => {
    const value = normalize(raw);
    if (!value) return;
    const exists = values.some((item) => item.toLowerCase() === value.toLowerCase());
    if (!exists) {
      onChange([...values, value]);
    }
    setInputValue("");
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addValue(inputValue);
    } else if (event.key === "Backspace" && !inputValue && values.length > 0) {
      onChange(values.slice(0, -1));
    }
  };

  const removeValue = (index: number) => {
    onChange(values.filter((_, i) => i !== index));
  };

  return (
    <div
      className={cn(
        "min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100",
        disabled && "opacity-60 pointer-events-none",
        className
      )}
    >
      <div className="flex flex-wrap gap-2">
        {values.map((value, index) => (
          <Chip key={`${value}-${index}`} onRemove={() => removeValue(index)}>
            {value}
          </Chip>
        ))}
        <Input
          id={id}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => addValue(inputValue)}
          placeholder={values.length === 0 ? placeholder : ""}
          disabled={disabled}
          className="h-8 min-w-[140px] flex-1 border-0 bg-transparent px-1 py-0 shadow-none focus-visible:ring-0"
        />
      </div>
    </div>
  );
}
