/**
 * Shared Framer Motion helpers for the premium landing sections.
 *
 * EASE_OUT is a cubic-bezier typed as a 4-tuple so framer-motion v12's
 * strict `Easing` type accepts it. Reused across hero, cards, and
 * revealed grids so the whole page feels cohesive.
 */
import type { Variants } from 'framer-motion';

export const EASE_OUT: [number, number, number, number] = [0.16, 1, 0.3, 1];

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE_OUT } },
};
