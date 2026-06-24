"use client";

import React, { useId } from "react";

type SparklineProps = {
  data: { date: string; count: number }[];
  className?: string;
};

export default function MentionSparkline({ data, className = "" }: SparklineProps) {
  const gradientId = useId();
  const max = Math.max(1, ...data.map((d) => d.count));
  const width = 120;
  const height = 32;
  const padding = 2;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  if (data.length === 0) {
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className={className}
        aria-hidden
      >
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          className="stroke-slate-200"
          strokeWidth={1}
        />
      </svg>
    );
  }

  const points = data.map((point, i) => ({
    x: padding + (i / Math.max(data.length - 1, 1)) * chartWidth,
    y: height - padding - (point.count / max) * chartHeight,
  }));

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ");

  const last = points[points.length - 1];
  const first = points[0];
  const areaPath = `${linePath} L ${last.x.toFixed(2)} ${height - padding} L ${first.x.toFixed(2)} ${height - padding} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      aria-hidden
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgb(99 102 241)" stopOpacity={0.35} />
          <stop offset="100%" stopColor="rgb(99 102 241)" stopOpacity={0.04} />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradientId})`} />
      <path
        d={linePath}
        fill="none"
        className="stroke-indigo-500"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
