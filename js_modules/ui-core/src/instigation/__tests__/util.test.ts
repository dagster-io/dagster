import {buildInstigationTick} from '../../graphql/builders';
import {InstigationTickStatus} from '../../graphql/types';
import {
  getTickResultType,
  isStuckStartedTick,
  mostSevereTickStatus,
  tickSummaryRank,
} from '../util';

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

describe('getTickResultType', () => {
  it('shows materializations for a tick that requested materializations', () => {
    // Declarative-automation tick (e.g. opened from a run, where the run is a backfill).
    expect(getTickResultType({requestedAssetMaterializationCount: 3})).toBe('materializations');
  });

  it('shows runs for a tick that requested no materializations', () => {
    // Plain sensor/schedule tick that launched runs.
    expect(getTickResultType({requestedAssetMaterializationCount: 0})).toBe('runs');
  });
});

describe('mostSevereTickStatus', () => {
  const ticks = (...statuses: InstigationTickStatus[]) => statuses.map((status) => ({status}));

  it('surfaces a failure batched alongside quieter ticks', () => {
    expect(
      mostSevereTickStatus(
        ticks(
          InstigationTickStatus.SKIPPED,
          InstigationTickStatus.FAILURE,
          InstigationTickStatus.SUCCESS,
        ),
      ),
    ).toBe(InstigationTickStatus.FAILURE);
  });

  it('prefers a success over an in-progress or skipped tick', () => {
    expect(
      mostSevereTickStatus(
        ticks(
          InstigationTickStatus.SKIPPED,
          InstigationTickStatus.STARTED,
          InstigationTickStatus.SUCCESS,
        ),
      ),
    ).toBe(InstigationTickStatus.SUCCESS);
  });

  it('reports skipped for an all-skipped or empty batch', () => {
    expect(mostSevereTickStatus(ticks(InstigationTickStatus.SKIPPED))).toBe(
      InstigationTickStatus.SKIPPED,
    );
    expect(mostSevereTickStatus([])).toBe(InstigationTickStatus.SKIPPED);
  });
});

describe('tickSummaryRank', () => {
  const rank = (
    status: InstigationTickStatus,
    counts: {requestedAssetMaterializationCount?: number; runIds?: string[]} = {},
  ) => tickSummaryRank({status, ...counts}, 'runs');

  it('sorts a failure ahead of a tick that requested runs, and both ahead of a skip', () => {
    const failed = rank(InstigationTickStatus.FAILURE);
    const requested = rank(InstigationTickStatus.SUCCESS, {runIds: ['a']});
    const skipped = rank(InstigationTickStatus.SKIPPED, {runIds: []});

    expect(failed).toBeLessThan(requested);
    expect(requested).toBeLessThan(skipped);
  });

  it('keeps a successful tick above the skipped ones even when it requested nothing', () => {
    expect(rank(InstigationTickStatus.SUCCESS, {runIds: []})).toBeLessThan(
      rank(InstigationTickStatus.SKIPPED, {runIds: []}),
    );
  });

  it('counts materializations rather than runs for a materialization tick', () => {
    const tick = {
      status: InstigationTickStatus.SKIPPED,
      requestedAssetMaterializationCount: 3,
      runIds: [],
    };

    expect(tickSummaryRank(tick, 'materializations')).toBeLessThan(
      tickSummaryRank({...tick, requestedAssetMaterializationCount: 0}, 'materializations'),
    );
  });
});
