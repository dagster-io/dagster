import {DynamicPartitionsRequestType, InstigationTickStatus} from '../graphql/types';
import type {TickResultType} from '../ticks/TickStatusTag';

type DynamicPartitionsRequestResult = {
  partitionKeys: string[] | null;
  type: DynamicPartitionsRequestType;
};

type InstigationTick = {
  timestamp: number;
  endTimestamp: number | null;
  status: InstigationTickStatus;
};

const TRUNCATION_THRESHOLD = 100;
const TRUNCATION_BUFFER = 5;

const THREE_DAYS_MS = 60 * 60 * 24 * 3 * 1000;

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
      tick.timestamp * 1000 < Date.now() - THREE_DAYS_MS)
  );
}

export function countPartitionsAddedOrDeleted(
  requests: Pick<DynamicPartitionsRequestResult, 'partitionKeys' | 'type'>[],
  type: DynamicPartitionsRequestType,
) {
  return requests.reduce((sum, request) => {
    if (request.type === type) {
      return sum + (request.partitionKeys?.length || 0);
    }
    return sum;
  }, 0);
}

/**
 * Decide which view the tick details dialog should show.
 *
 * When the "run" that was createed is a backfill, the runs view can't render (400s when its backfill ID is passed to the
 * runs feed as a run UUID). So when a tick requested any materializations, show the materializations view; otherwise show
 * the runs view.
 */
export function getTickResultType(tick: {
  requestedAssetMaterializationCount: number;
}): TickResultType {
  return tick.requestedAssetMaterializationCount > 0 ? 'materializations' : 'runs';
}

// Batched ticks are drawn as one mark, which reports the most severe status it covers so a
// single failure stays visible alongside hundreds of skipped ticks.
const STATUS_SEVERITY = [
  InstigationTickStatus.FAILURE,
  InstigationTickStatus.SUCCESS,
  InstigationTickStatus.STARTED,
  InstigationTickStatus.SKIPPED,
];

export function mostSevereTickStatus(ticks: Pick<InstigationTick, 'status'>[]) {
  const statuses = new Set(ticks.map((tick) => tick.status));
  return STATUS_SEVERITY.find((status) => statuses.has(status)) ?? InstigationTickStatus.SKIPPED;
}

type TickResultCounts = {
  requestedAssetMaterializationCount?: number;
  runIds?: string[];
};

export function countForTick(tick: TickResultCounts, tickResultType: TickResultType): number {
  if (tickResultType === 'materializations' || !('runIds' in tick)) {
    return tick.requestedAssetMaterializationCount ?? 0;
  }
  return tick.runIds?.length ?? 0;
}

// Rank of the ticks that neither failed nor requested anything.
export const TICK_SUMMARY_RANK_QUIET = 2;

// Orders a batch of ticks by what a reader is looking for: a failure, then anything that
// requested work, then the quiet ones. A capped list should never hide the tick that
// explains the batch's color.
export function tickSummaryRank(
  tick: Pick<InstigationTick, 'status'> & TickResultCounts,
  tickResultType: TickResultType,
): number {
  if (tick.status === InstigationTickStatus.FAILURE) {
    return 0;
  }
  if (countForTick(tick, tickResultType) > 0 || tick.status === InstigationTickStatus.SUCCESS) {
    return 1;
  }
  return TICK_SUMMARY_RANK_QUIET;
}
