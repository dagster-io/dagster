const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

// Intervals that read as round clock times. Snapping to these keeps labels on values a person
// would pick (5:45, 5:50) rather than wherever the visible range happens to divide.
const NICE_INTERVALS = [
  SECOND,
  5 * SECOND,
  10 * SECOND,
  15 * SECOND,
  30 * SECOND,
  MINUTE,
  2 * MINUTE,
  5 * MINUTE,
  10 * MINUTE,
  15 * MINUTE,
  30 * MINUTE,
  HOUR,
  2 * HOUR,
  3 * HOUR,
  6 * HOUR,
  12 * HOUR,
  24 * HOUR,
];

const LONGEST_INTERVAL = 24 * HOUR;

// Unlabeled gridlines closer together than this read as hatching rather than a grid.
const MIN_MINOR_SPACING_PX = 40;

const MAX_TICKS = 500;

export interface TimeAxisTick {
  time: number;
  // Major ticks are the ones worth labeling; the rest subdivide the space between them.
  isMajor: boolean;
}

export interface TimeAxis {
  // Spacing of the major ticks, which also says how precise a label needs to be.
  intervalMs: number;
  ticks: TimeAxisTick[];
}

/**
 * Lay out gridlines for a time range, snapped to round clock intervals.
 *
 * Ticks land on multiples of the interval since the epoch, which is a round local time in any
 * timezone offset by a whole hour, and for the sub-hour intervals in any half-hour offset too.
 */
export function buildTimeAxis({
  start,
  end,
  width,
  minLabelSpacingPx,
  minIntervalMs = 0,
}: {
  start: number;
  end: number;
  width: number;
  // How much room a label needs, which sets how far apart the major ticks can be.
  minLabelSpacingPx: number;
  // Floor on the major interval, for callers whose data is coarser than the pixels allow.
  minIntervalMs?: number;
}): TimeAxis {
  const range = end - start;
  if (range <= 0 || width <= 0) {
    return {intervalMs: 0, ticks: []};
  }

  const pxPerMs = width / range;
  const wanted = Math.max(minLabelSpacingPx / pxPerMs, minIntervalMs);
  const major = NICE_INTERVALS.find((interval) => interval >= wanted) ?? LONGEST_INTERVAL;

  // The densest round subdivision of the major interval that still reads as separate lines.
  const minor =
    NICE_INTERVALS.find(
      (interval) =>
        interval < major && major % interval === 0 && interval * pxPerMs >= MIN_MINOR_SPACING_PX,
    ) ?? major;

  const ticks: TimeAxisTick[] = [];
  for (
    let time = Math.ceil(start / minor) * minor;
    time <= end && ticks.length < MAX_TICKS;
    time += minor
  ) {
    ticks.push({time, isMajor: time % major === 0});
  }

  return {intervalMs: major, ticks};
}
