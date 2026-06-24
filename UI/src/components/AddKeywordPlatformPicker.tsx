"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Platform } from "@/lib/enums";
import { platforms } from "@/lib/platforms";

type AddKeywordPlatformPickerProps = {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (platform: Platform) => void;
};

export default function AddKeywordPlatformPicker({
  isOpen,
  onClose,
  onSelect,
}: AddKeywordPlatformPickerProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-white">
        <DialogHeader>
          <DialogTitle>Choose platform</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-slate-500 mb-4">
          Where should we monitor this keyword?
        </p>
        <div className="grid grid-cols-2 gap-3">
          {platforms.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                onSelect(p.id);
                onClose();
              }}
              className="flex items-center gap-3 rounded-xl border border-slate-200 p-4 text-left hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors"
            >
              <div className={`p-2 rounded-lg bg-slate-50 ${p.color}`}>{p.icon}</div>
              <span className="font-medium text-slate-900">{p.name}</span>
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
