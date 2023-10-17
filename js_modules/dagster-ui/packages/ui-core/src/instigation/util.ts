import {InstigationTick, InstigationTickStatus} from '../graphql/types';

const TRUNCATION_THRESHOLD = 100;
const TRUNCATION_BUFFER = 5;

export const truncate = (str: string) =>
  str.length > TRUNCATION_THRESHOLD
    ? `${str.slice(0, TRUNCATION_THRESHOLD - TRUNCATION_BUFFER)}…`
    : str;

export function isOldTickWithoutEndtimestamp(
  tick: Pick<InstigationTick, 'timestamp' | 'endTimestamp' | 'status'>,
) {
  return tick.status !== InstigationTickStatus.STARTED && !tick.endTimestamp;
}
