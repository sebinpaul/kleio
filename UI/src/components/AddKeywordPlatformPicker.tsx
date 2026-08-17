"use client";

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Platform } from "@/lib/enums";
import { platforms } from "@/lib/platforms";

type AddKeywordPlatformPickerProps = {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (platforms: Platform[]) => void;
};

export default function AddKeywordPlatformPicker({
  isOpen,
  onClose,
  onSelect,
}: AddKeywordPlatformPickerProps) {
  const [selected, setSelected] = useState<Platform[]>([]);

  useEffect(() => {
    if (isOpen) setSelected([]);
  }, [isOpen]);

  const allIds = platforms.map((p) => p.id);
  const allSelected = selected.length === allIds.length;

  const toggle = (id: Platform) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    setSelected(allSelected ? [] : [...allIds]);
  };

  const handleContinue = () => {
    if (selected.length === 0) return;
    onSelect(selected);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-white">
        <DialogHeader>
          <DialogTitle>Choose platforms</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-slate-500 mb-3">
          Select where this keyword should be monitored. You can pick one, several, or all.
        </p>

        <div className="flex items-center justify-between mb-3">
          <button
            type="button"
            onClick={toggleAll}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            {allSelected ? "Clear all" : "Select all"}
          </button>
          <span className="text-xs text-slate-500">
            {selected.length} selected
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {platforms.map((p) => {
            const isSelected = selected.includes(p.id);
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => toggle(p.id)}
                aria-pressed={isSelected}
                className={`flex items-center gap-3 rounded-xl border p-4 text-left transition-colors ${
                  isSelected
                    ? "border-indigo-400 bg-indigo-50 ring-1 ring-indigo-200"
                    : "border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50"
                }`}
              >
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-600 text-white"
                      : "border-slate-300 bg-white"
                  }`}
                >
                  {isSelected && (
                    <svg className="h-3.5 w-3.5" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M2 6l3 3 5-5"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </div>
                <div className={`p-2 rounded-lg bg-slate-50 ${p.color}`}>{p.icon}</div>
                <span className="font-medium text-slate-900">{p.name}</span>
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleContinue}
            disabled={selected.length === 0}
            className="gradient-button"
          >
            Continue
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
