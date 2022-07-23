export interface RunWithTime {
  startTime: number;
  endTime: number;
}

export type RunBatch<R extends RunWithTime> = {
  runs: R[];
  startTime: number;
  endTime: number;
  left: number;
  width: number;
};

type Config<R extends RunWithTime> = {
  runs: R[];
  start: number;
  end: number;
  width: number;
  minChunkWidth: number;
  minMultipleWidth: number;
};

export const overlap = (a: {start: number; end: number}, b: {start: number; end: number}) =>
  !(a.end < b.start || b.end < a.start);

/**
 * Given a list of runs, batch any that overlap. Calculate `left` and `width` values for rendering
 * purposes, using minimum widths for very brief runs and overlapping batches.
 */
export const batchRunsForTimeline = <R extends RunWithTime>(config: Config<R>) => {
  const {runs, start, end, width, minChunkWidth, minMultipleWidth} = config;
  const rangeLength = end - start;

  const batches: RunBatch<R>[] = runs
    .map((run) => {
      const startTime = run.startTime;
      const endTime = run.endTime || Date.now();
      const left = Math.max(0, Math.floor(((startTime - start) / rangeLength) * width));
      const runWidth = Math.max(
        minChunkWidth,
        Math.min(
          Math.ceil(((endTime - startTime) / rangeLength) * width),
          Math.ceil(((endTime - start) / rangeLength) * width),
        ),
      );

      return {
        runs: [run],
        startTime,
        endTime,
        left,
        width: runWidth,
      };
    })
    .sort((a, b) => b.left - a.left);

  const consolidated = [];
  while (batches.length) {
    const current = batches.shift();
    const next = batches[0];
    if (current) {
      if (
        next &&
        overlap(
          {
            start: current.left,
            end: current.left + Math.max(current.width, minMultipleWidth),
          },
          {start: next.left, end: next.left + Math.max(next.width, minMultipleWidth)},
        )
      ) {
        // Remove `next`, consolidate it with `current`, and unshift it back on.
        // This way, we keep looking for batches to consolidate with.
        batches.shift();
        current.runs = [...current.runs, ...next.runs];
        current.startTime = Math.min(current.startTime, next.startTime);
        current.endTime = Math.max(current.endTime, next.endTime);

        // Identify the rightmost point for these two items.
        const right = Math.max(
          current.left + minMultipleWidth,
          current.left + current.width,
          next.left + next.width,
        );

        // Using the leftmost point, calculate the new width using the rightmost point
        // determined above.
        const minLeft = Math.min(current.left, next.left);
        current.width = right - minLeft;
        current.left = minLeft;

        batches.unshift(current);
      } else {
        // If the next batch doesn't overlap, we've consolidated this batch
        // all we can. Move on!
        consolidated.push(current);
      }
    }
  }

  return consolidated;
};
