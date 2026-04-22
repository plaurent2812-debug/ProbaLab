import { useId, useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface SparklineProps {
  series: number[];
  color?: string;
  height?: number;
  width?: number;
}

/**
 * Minimal sparkline with on-enter path-draw animation + soft gradient fill.
 * Pure SVG, no external chart library. Width/height are fixed so the
 * component composes cleanly inside a flex row.
 */
export function Sparkline({
  series,
  color = '#10b981',
  height = 40,
  width = 120,
}: SparklineProps) {
  const ref = useRef<SVGSVGElement>(null);
  const inView = useInView(ref, { once: true, margin: '-20%' });
  // Unique per-instance gradient id avoids collisions when the same
  // component appears multiple times in one tree.
  const gradId = useId();

  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;
  const step = width / Math.max(series.length - 1, 1);
  const points = series
    .map((v, i) => `${i * step},${height - ((v - min) / range) * height}`)
    .join(' ');

  return (
    <svg ref={ref} width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
        initial={{ pathLength: 0 }}
        animate={inView ? { pathLength: 1 } : { pathLength: 0 }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
      />
      <motion.polygon
        fill={`url(#${gradId})`}
        points={`0,${height} ${points} ${width},${height}`}
        initial={{ opacity: 0 }}
        animate={inView ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1.2, delay: 0.3 }}
      />
    </svg>
  );
}
