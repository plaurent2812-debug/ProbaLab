import { describe, it, expect } from 'vitest'
import { getStatValue, formatProba, formatOdds, formatEV } from '../statsHelper'

// ---------------------------------------------------------------------------
// formatProba
// ---------------------------------------------------------------------------
// The function receives values already expressed as percentages (0-100 scale),
// e.g. 73.4 → "73%". It does NOT multiply by 100 internally.
describe('formatProba', () => {
  it('rounds a percentage-scale value to a whole-number percent string', () => {
    expect(formatProba(73.4)).toBe('73%')
  })

  it('rounds 72.5 up to 73%', () => {
    expect(formatProba(72.5)).toBe('73%')
  })

  it('formats 100 as "100%"', () => {
    expect(formatProba(100)).toBe('100%')
  })

  it('formats 0 as "0%"', () => {
    expect(formatProba(0)).toBe('0%')
  })

  it('formats a value with many decimals correctly', () => {
    expect(formatProba(45.678)).toBe('46%')
  })

  it('returns "—" for null', () => {
    expect(formatProba(null)).toBe('—')
  })

  it('returns "—" for undefined', () => {
    expect(formatProba(undefined)).toBe('—')
  })
})

// ---------------------------------------------------------------------------
// formatOdds
// ---------------------------------------------------------------------------
describe('formatOdds', () => {
  it('formats an odds value to 2 decimal places', () => {
    expect(formatOdds(2.5)).toBe('2.50')
  })

  it('formats integer odds with trailing zeros', () => {
    expect(formatOdds(3)).toBe('3.00')
  })

  it('truncates without rounding when already at 2 decimals', () => {
    expect(formatOdds(1.75)).toBe('1.75')
  })

  it('returns "—" for null', () => {
    expect(formatOdds(null)).toBe('—')
  })

  it('returns "—" for undefined', () => {
    expect(formatOdds(undefined)).toBe('—')
  })
})

// ---------------------------------------------------------------------------
// formatEV
// ---------------------------------------------------------------------------
describe('formatEV', () => {
  it('formats a positive EV with a leading "+" sign', () => {
    expect(formatEV(0.12)).toBe('+12.0%')
  })

  it('formats a negative EV without a "+" sign', () => {
    expect(formatEV(-0.05)).toBe('-5.0%')
  })

  it('formats zero EV as "+0.0%"', () => {
    expect(formatEV(0)).toBe('+0.0%')
  })

  it('formats small positive EV correctly', () => {
    expect(formatEV(0.003)).toBe('+0.3%')
  })

  it('returns "—" for null', () => {
    expect(formatEV(null)).toBe('—')
  })

  it('returns "—" for undefined', () => {
    expect(formatEV(undefined)).toBe('—')
  })
})

// ---------------------------------------------------------------------------
// getStatValue
// ---------------------------------------------------------------------------
describe('getStatValue', () => {
  it('reads a value from stats_json first when both are present', () => {
    const prediction = {
      proba_home: 50,
      stats_json: { proba_home: 65 },
    }
    expect(getStatValue(prediction, 'proba_home')).toBe(65)
  })

  it('falls back to the top-level field when stats_json lacks the key', () => {
    const prediction = {
      proba_home: 42,
      stats_json: {},
    }
    expect(getStatValue(prediction, 'proba_home')).toBe(42)
  })

  it('returns null (default fallback) when key is absent everywhere', () => {
    const prediction = { stats_json: {} }
    expect(getStatValue(prediction, 'proba_home')).toBeNull()
  })

  it('returns a custom fallback when key is absent', () => {
    const prediction = { stats_json: {} }
    expect(getStatValue(prediction, 'proba_home', 0)).toBe(0)
  })

  it('normalises underscore-separated digits — proba_over_2_5 matches proba_over_25', () => {
    const prediction = {
      stats_json: { proba_over_25: 58 },
    }
    // The helper should find proba_over_25 when asked for proba_over_2_5
    expect(getStatValue(prediction, 'proba_over_2_5')).toBe(58)
  })

  it('normalises condensed digits — proba_over_25 matches proba_over_2_5 in top-level', () => {
    const prediction = {
      proba_over_25: 72,
      stats_json: {},
    }
    // Asked for the _2_5 variant, should find proba_over_25 on top-level
    expect(getStatValue(prediction, 'proba_over_2_5')).toBe(72)
  })

  it('ignores non-numeric values in stats_json', () => {
    const prediction = {
      proba_home: 55,
      stats_json: { proba_home: 'high' }, // string — should be skipped
    }
    expect(getStatValue(prediction, 'proba_home')).toBe(55)
  })

  it('handles a null prediction gracefully', () => {
    expect(getStatValue(null, 'proba_home', -1)).toBe(-1)
  })
})
