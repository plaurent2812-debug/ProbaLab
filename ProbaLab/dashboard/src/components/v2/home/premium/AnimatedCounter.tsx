import { useEffect, useRef } from 'react';
import { motion, useInView, useMotionValue, useSpring, useTransform } from 'framer-motion';

interface CounterProps {
  to: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
}

/**
 * Animated numeric counter triggered on viewport entry.
 *
 * Framer's `useSpring` drives a motion value from 0 → `to` once, the
 * first time the element enters the viewport. Uses `tabular-nums` on
 * the consumer side to prevent width jitter as digits change.
 */
export function AnimatedCounter({
  to,
  decimals = 1,
  suffix = '',
  prefix = '',
  duration = 1.2,
}: CounterProps) {
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { duration: duration * 1000, bounce: 0 });
  const rounded = useTransform(
    springValue,
    (v) => `${prefix}${v.toFixed(decimals)}${suffix}`,
  );
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-20%' });

  useEffect(() => {
    if (inView) motionValue.set(to);
  }, [inView, motionValue, to]);

  return <motion.span ref={ref}>{rounded}</motion.span>;
}
