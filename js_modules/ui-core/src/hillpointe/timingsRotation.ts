import {useStateWithStorage} from '../hooks/useStateWithStorage';

// Job timings cycles through the jobs of this code location on its own.
export const ROTATE_LOCATION = 'live';
export const ROTATE_MAX_SECS = 120;
const ROTATE_DEFAULT_SECS = 30;
const ROTATE_STORAGE_KEY = 'hillpointe-timings-rotate-secs';

/** Seconds each job stays on screen before the next one shows; 0 turns rotation off. */
export const useTimingsRotateSecs = () =>
  useStateWithStorage<number>(ROTATE_STORAGE_KEY, (value) =>
    typeof value === 'number' && value >= 0 && value <= ROTATE_MAX_SECS
      ? value
      : ROTATE_DEFAULT_SECS,
  );

/** The job to show after `current`, wrapping around; the first one if `current` is not listed. */
export const nextInRotation = (names: string[], current: string | null) =>
  names[(names.indexOf(current ?? '') + 1) % names.length] ?? null;
