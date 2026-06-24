"use client";

import React from "react";
import { HelpCircle } from "lucide-react";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type FieldLabelProps = {
  htmlFor?: string;
  label: string;
  tooltip: string;
  required?: boolean;
  className?: string;
};

export default function FieldLabel({
  htmlFor,
  label,
  tooltip,
  required = false,
  className,
}: FieldLabelProps) {
  return (
    <div className={`flex items-center gap-2 ${className || ""}`}>
      <Label htmlFor={htmlFor} className="text-base font-medium text-slate-900">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </Label>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="text-slate-400 hover:text-slate-600"
            aria-label={`Help: ${label}`}
          >
            <HelpCircle className="size-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent>{tooltip}</TooltipContent>
      </Tooltip>
    </div>
  );
}
