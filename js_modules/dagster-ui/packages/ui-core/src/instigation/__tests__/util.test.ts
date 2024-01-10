import {InstigationTickStatus, buildInstigationTick} from '../../graphql/types';
import {isStuckStartedTick} from '../util';

const DAY = 1000 * 60 * 60 * 24;

describe('isStuckStarted', () => {
  it('identifies stuck started ticks', () => {
    const todayTickStarted = buildInstigationTick({
      status: InstigationTickStatus.STARTED,
      timestamp: Date.now(),
      endTimestamp: null,
    });

    // First index so can't tell if its stuck
    expect(isStuckStartedTick(todayTickStarted, 0)).toBe(false);

    // Second index so definitely stuck
    expect(isStuckStartedTick(todayTickStarted, 1)).toBe(true);

    const overThreeDaysOldTickStarted = buildInstigationTick({
      status: InstigationTickStatus.STARTED,
      timestamp: (Date.now() - 4 * DAY) / 1000,
      endTimestamp: null,
    });

    // Over three days old so probably stuck
    expect(isStuckStartedTick(overThreeDaysOldTickStarted, 0)).toBe(true);

    const todayTickFailure = buildInstigationTick({
      status: InstigationTickStatus.FAILURE,
      timestamp: Date.now() / 1000,
      endTimestamp: Date.now() / 1000,
    });

    expect(isStuckStartedTick(todayTickFailure, 0)).toBe(false);
    expect(isStuckStartedTick(todayTickFailure, 1)).toBe(false);
  });
});
