"use client"

import { useEffect, useRef } from "react"
import type React from "react"
import { useInView } from "motion/react"
import { annotate } from "rough-notation"
import { type RoughAnnotation } from "rough-notation/lib/model"

type AnnotationAction =
  | "highlight"
  | "underline"
  | "box"
  | "circle"
  | "strike-through"
  | "crossed-off"
  | "bracket"

interface HighlighterProps {
  children: React.ReactNode
  action?: AnnotationAction
  color?: string
  strokeWidth?: number
  animationDuration?: number
  iterations?: number
  padding?: number
  multiline?: boolean
  isView?: boolean
  delay?: number
}

export function Highlighter({
  children,
  action = "highlight",
  color = "#ffd1dc",
  strokeWidth = 1.5,
  animationDuration = 600,
  iterations = 2,
  padding = 2,
  multiline = true,
  isView = true,
  delay = 0,
}: HighlighterProps) {
  const elementRef = useRef<HTMLSpanElement>(null)
  const annotationRef = useRef<RoughAnnotation | null>(null)

  const isInView = useInView(elementRef, {
    once: true,
    margin: "-10%",
  })

  const shouldShow = !isView || isInView

  useEffect(() => {
    if (!shouldShow) return
    const element = elementRef.current
    if (!element || annotationRef.current) return

    const timer = setTimeout(() => {
      if (annotationRef.current) return
      const annotation = annotate(element, {
        type: action,
        color,
        strokeWidth,
        animationDuration,
        iterations,
        padding,
        multiline,
      })
      annotationRef.current = annotation
      annotation.show()
    }, delay)

    return () => clearTimeout(timer)
  }, [shouldShow, delay, action, color, strokeWidth, animationDuration, iterations, padding, multiline])

  return (
    <span ref={elementRef} className="relative inline-block bg-transparent">
      {children}
    </span>
  )
}
