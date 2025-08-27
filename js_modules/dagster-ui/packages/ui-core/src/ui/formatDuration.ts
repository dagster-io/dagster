interface DurationOptions {
  /** Maximum value before the next unit is displayed */
  maxValueBeforeNextUnit?: Record<UnitType, number>;
  /** Number of significant units to display (1 or 2) */
  significantUnits?: 1 | 2;
  /** Whether the input is in seconds (default: false, assumes milliseconds) */
  unit?: 'seconds' | 'milliseconds';
}

type UnitType = 'year' | 'month' | 'week' | 'day' | 'hour' | 'minute' | 'second' | 'millisecond';
type PluralUnitType = `${UnitType}s`;

const defaultMaxValueBeforeNextUnit: Record<UnitType, number> = {
  year: Infinity,
  month: 24,
  week: 8,
  day: 14,
  hour: 48,
  minute: 120,
  second: 120,
  millisecond: 500,
};

interface DurationPart {
  value: number;
  unit: UnitType | PluralUnitType;
}

const YEAR_MS = 365 * 24 * 60 * 60 * 1000;
const MONTH_MS = 30 * 24 * 60 * 60 * 1000;
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;
const MINUTE_MS = 60 * 1000;
const SECOND_MS = 1000;

const UNITS: Array<[number, UnitType, PluralUnitType]> = [
  [YEAR_MS, 'year', 'years'],
  [MONTH_MS, 'month', 'months'],
  [WEEK_MS, 'week', 'weeks'],
  [DAY_MS, 'day', 'days'],
  [HOUR_MS, 'hour', 'hours'],
  [MINUTE_MS, 'minute', 'minutes'],
  [SECOND_MS, 'second', 'seconds'],
  [1, 'millisecond', 'milliseconds'],
];

export const unitToShortLabel: Record<UnitType | PluralUnitType, string> = {
  year: 'yr',
  years: 'yr',
  month: 'mo',
  months: 'mo',
  week: 'wk',
  weeks: 'wk',
  day: 'day',
  days: 'days',
  hour: 'hr',
  hours: 'hr',
  minute: 'min',
  minutes: 'min',
  second: 'sec',
  seconds: 'sec',
  millisecond: 'ms',
  milliseconds: 'ms',
};

type NonEmptyArray<T> = [T, ...T[]];

/**
 * Converts a duration in milliseconds or seconds to a human-readable format
 * @param duration - The duration in milliseconds (default) or seconds
 * @param options - Configuration options
 * @returns Human-readable duration string
 */
export function formatDuration(
  duration: number,
  options: DurationOptions = {},
): NonEmptyArray<DurationPart> {
  const {
    maxValueBeforeNextUnit = defaultMaxValueBeforeNextUnit,
    significantUnits = 1,
    unit = 'milliseconds',
  } = options;

  // Convert to milliseconds if input is in seconds
  const ms = unit === 'seconds' ? duration * 1000 : duration;

  // Handle edge cases
  if (ms <= 0) {
    return [{value: 0, unit: 'milliseconds'}];
  }

  // Special case: Check if duration represents exactly 1 year, 1 month, or 1 week
  for (const [unitMs, singular] of UNITS) {
    if (ms === unitMs) {
      return [{value: 1, unit: singular}];
    }
  }

  const parts: DurationPart[] = [];
  let remainingMs = ms;

  let bestUnit: [number, UnitType, PluralUnitType] | null = null;
  let bestValue = 0;

  const roundFn = significantUnits > 1 ? Math.floor : (x: number) => x;

  if (remainingMs > DAY_MS) {
    let violatingUnitIndex = -1;

    for (let i = 0; i < UNITS.length; i++) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const [unitMs, singular] = UNITS[i]!;
      const value = roundFn(remainingMs / unitMs);
      const threshold = maxValueBeforeNextUnit[singular];
      if (value >= threshold) {
        violatingUnitIndex = i;
        break;
      }
    }

    if (violatingUnitIndex !== -1) {
      if (violatingUnitIndex > 0) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const nextLargerUnit = UNITS[violatingUnitIndex - 1]!;
        if (nextLargerUnit) {
          const [unitMs, singular, plural] = nextLargerUnit;
          const value = roundFn(remainingMs / unitMs);
          if (value >= 1) {
            bestUnit = [unitMs, singular, plural];
            bestValue = value;
          }
        }
      }
    }
  }

  if (!bestUnit) {
    for (const [unitMs, singular, plural] of UNITS) {
      const value = roundFn(remainingMs / unitMs);
      if (value >= 1) {
        bestUnit = [unitMs, singular, plural];
        bestValue = value;
        break;
      }
    }
  }

  // Use the selected unit
  if (bestUnit && bestValue > 0) {
    const [unitMs, singular, plural] = bestUnit;
    parts.push({
      value: bestValue,
      unit: bestValue === 1 ? singular : plural,
    });

    remainingMs -= bestValue * unitMs;

    // If we need more significant units and have remaining time
    if (significantUnits > 1 && remainingMs > 0) {
      for (const [unitMs, singular, plural] of UNITS) {
        if (unitMs >= bestUnit[0]) {
          continue;
        } // Skip same or larger units

        const roundFn = parts.length - 1 === significantUnits ? (x: number) => x : Math.floor;
        const value = roundFn(remainingMs / unitMs);
        if (value > 0) {
          parts.push({
            value,
            unit: value === 1 ? singular : plural,
          });
          break;
        }
      }
    }
  } else {
    // Fallback: if no parts were found, return 0 milliseconds
    return [{value: 0, unit: 'milliseconds'}];
  }

  return parts as NonEmptyArray<DurationPart>;
}
