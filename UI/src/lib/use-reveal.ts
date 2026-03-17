"use client";

import { useEffect, useRef, type RefObject } from "react";

let observer: IntersectionObserver | null = null;
const entries = new WeakMap<Element, { delay: number }>();

function getObserver() {
  if (observer) return observer;
  observer = new IntersectionObserver(
    (items) => {
      for (const entry of items) {
        if (!entry.isIntersecting) continue;
        const el = entry.target as HTMLElement;
        const meta = entries.get(el);
        const delay = meta?.delay ?? 0;
        if (delay > 0) {
          el.style.animationDelay = `${delay}ms`;
        }
        el.classList.add("revealed");
        observer!.unobserve(el);
        entries.delete(el);
      }
    },
    { rootMargin: "-60px" },
  );
  return observer;
}

export function useReveal<T extends HTMLElement = HTMLDivElement>(
  delay = 0,
): RefObject<T | null> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    entries.set(el, { delay });
    getObserver().observe(el);
    return () => {
      getObserver().unobserve(el);
      entries.delete(el);
    };
  }, [delay]);

  return ref;
}
