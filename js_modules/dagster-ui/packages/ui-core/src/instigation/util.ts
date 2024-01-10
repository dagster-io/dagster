import {InstigationTick, InstigationTickStatus} from '../graphql/types';

const TRUNCATION_THRESHOLD = 100;
const TRUNCATION_BUFFER = 5;

const THREE_DAYS = 60 * 60 * 24 * 3;

export const truncate = (str: string) =>
  str.length > TRUNCATION_THRESHOLD
    ? `${str.slice(0, TRUNCATION_THRESHOLD - TRUNCATION_BUFFER)}…`
    : str;

export function isStuckStartedTick(
  tick: Pick<InstigationTick, 'timestamp' | 'endTimestamp' | 'status'>,
  index: number,
) {
  return (
    !tick.endTimestamp &&
    // If the index is 0 and the tick does have an end timestamp then we can't know if its actually stuck or still in progress
    // but if its older than three days then its very likely stuck
    ((index !== 0 && tick.status === InstigationTickStatus.STARTED) ||
      tick.timestamp * 1000 < Date.now() - THREE_DAYS)
  );
}
