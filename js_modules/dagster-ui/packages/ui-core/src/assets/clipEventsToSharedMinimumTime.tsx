import min from 'lodash/min';

export function clipEventsToSharedMinimumTime<
  Mat extends {timestamp: string},
  Obs extends {timestamp: string},
>(materializations: Mat[], observations: Obs[], requestedLimit: number) {
  // If we load 100 observations and get [June 2024 back to Jan 2024], and load
  // 100 materializations and get [June 2024 back to March 2024], we want to keep
  // only the observations back to March so the user can't scroll through
  // [March -> Jan] with the materializations all missing.
  //
  // Note: If we have less than 100 datapoints in a dataset, no further pages are
  // available and we don't want to clip the other to the minimum timestamp.
  //
  const minMatTimestamp =
    materializations.length === requestedLimit
      ? min(materializations.map((e) => Number(e.timestamp))) || 0
      : 0;
  const minObsTimestamp =
    observations.length === requestedLimit
      ? min(observations.map((e) => Number(e.timestamp))) || 0
      : 0;

  const minToKeep = Math.max(minMatTimestamp, minObsTimestamp);

  return {
    materializations: materializations.filter((m) => Number(m.timestamp) >= minToKeep),
    observations: observations.filter((m) => Number(m.timestamp) >= minToKeep),
  };
}
