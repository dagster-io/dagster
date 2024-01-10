import {InstigationTickStatus, buildInstigationTick} from '../../graphql/types';
import {isStuckStartedTick} from '../util';

const DAY = 1000 * 60 * 60 * 24;

describe('isStuckStarted', () => {
  it('identifies stuck started ticks', () => {
    const startedTickTodayStarted = buildInstigationTick({
      status: InstigationTickStatus.STARTED,
      timestamp: Date.now(),
      endTimestamp: null,
    });

    // First index so can't tell if its stuck
    expect(isStuckStartedTick(startedTickTodayStarted, 0)).toBe(false);

    // Second index so definitely stuck
    expect(isStuckStartedTick(startedTickTodayStarted, 1)).toBe(true);

    const overThreeDaysOldTickStarted = buildInstigationTick({
      status: InstigationTickStatus.STARTED,
      timestamp: (Date.now() - 4 * DAY) / 1000,
      endTimestamp: null,
    });

    // Over three days old so probably stuck
    expect(isStuckStartedTick(overThreeDaysOldTickStarted, 0)).toBe(true);

    const startedTickTodayFailure = buildInstigationTick({
      status: InstigationTickStatus.FAILURE,
      timestamp: Date.now() / 1000,
      endTimestamp: Date.now() / 1000,
    });

    expect(isStuckStartedTick(startedTickTodayFailure, 0)).toBe(false);
    expect(isStuckStartedTick(startedTickTodayFailure, 1)).toBe(false);
  });
});
