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
  isView = false,
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
    const element = elementRef.current
    let resizeObserver: ResizeObserver | null = null
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | null = null

    if (shouldShow && element) {
      const draw = () => {
        if (cancelled) return

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

        resizeObserver = new ResizeObserver(() => {
          annotation.hide()
          annotation.show()
        })

        resizeObserver.observe(element)
      }

      document.fonts.ready.then(() => {
        if (cancelled) return
        if (delay > 0) {
          timer = setTimeout(draw, delay)
        } else {
          draw()
        }
      })
    }

    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
      if (annotationRef.current) {
        annotationRef.current.remove()
        annotationRef.current = null
      }
      if (resizeObserver) {
        resizeObserver.disconnect()
      }
    }
  }, [
    shouldShow,
    delay,
    action,
    color,
    strokeWidth,
    animationDuration,
    iterations,
    padding,
    multiline,
  ])

  return (
    <span ref={elementRef} className="relative inline-block bg-transparent">
      {children}
    </span>
  )
}
