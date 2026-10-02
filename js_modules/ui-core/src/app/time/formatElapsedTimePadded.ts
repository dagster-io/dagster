import {timeByParts} from '../timeByParts';

const pad = (value: number) => String(value).padStart(2, '0');

/** Zero-padded HH:MM:SS so counters and durations line up in a column; negatives read as zero. */
export const formatElapsedTimePadded = (ms: number) => {
  const {hours, minutes, seconds} = timeByParts(Math.max(0, ms));
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
};
