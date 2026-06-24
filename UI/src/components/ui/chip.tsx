import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

type ChipProps = {
  children: React.ReactNode
  onRemove?: () => void
  className?: string
}

export function Chip({ children, onRemove, className }: ChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-sm font-medium text-indigo-800",
        className
      )}
    >
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="rounded-full p-0.5 text-indigo-600 hover:bg-indigo-100 hover:text-indigo-900"
          aria-label="Remove"
        >
          <X className="size-3.5" />
        </button>
      )}
    </span>
  )
}
