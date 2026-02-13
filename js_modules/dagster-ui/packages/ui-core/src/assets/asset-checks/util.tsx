import {Colors, Icon, IconName, Spinner} from '@dagster-io/ui-components';

import {ExecuteChecksButtonCheckFragment} from './types/ExecuteChecksButton.types';
import {AssetCheckTableFragment} from './types/VirtualizedAssetCheckTable.types';
import {assertUnreachable} from '../../app/Util';
import {AssetCheckLiveFragment} from '../../asset-data/types/AssetBaseDataProvider.types';
import {AssetCheckExecutionResolvedStatus, AssetCheckSeverity} from '../../graphql/types';

// Type for checks that have partition status information
type AssetCheckWithPartitionStatuses = Pick<
  AssetCheckLiveFragment,
  'executionForLatestMaterialization' | 'partitionStatuses'
>;

export function assetCheckStatusDescription(
  check: AssetCheckTableFragment & ExecuteChecksButtonCheckFragment,
) {
  // Use aggregate status to handle partitioned checks correctly
  const aggregateStatus = getAggregateCheckIconType(check);

  switch (aggregateStatus) {
    case 'NOT_EVALUATED':
      return 'Not evaluated';
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
    case 'ERROR':
      return 'Failed';
    case AssetCheckExecutionResolvedStatus.FAILED:
    case 'WARN':
      return 'Failed';
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return 'In progress';
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return 'Skipped';
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return 'Succeeded';
    default:
      assertUnreachable(aggregateStatus);
  }
}

export function getCheckIcon(
  check: AssetCheckTableFragment & ExecuteChecksButtonCheckFragment,
): React.ReactNode {
  // Use aggregate status to handle partitioned checks correctly
  const aggregateStatus = getAggregateCheckIconType(check);
  const lastExecution = check.executionForLatestMaterialization;
  const isWarning = lastExecution?.evaluation?.severity === AssetCheckSeverity.WARN;

  switch (aggregateStatus) {
    case 'NOT_EVALUATED':
      return <Icon name="status" color={Colors.accentGray()} />;
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
    case 'ERROR':
      return <Icon name="cancel" color={isWarning ? Colors.accentYellow() : Colors.accentRed()} />;
    case AssetCheckExecutionResolvedStatus.FAILED:
    case 'WARN':
      if (isWarning || aggregateStatus === 'WARN') {
        return <Icon name="warning_outline" color={Colors.accentYellow()} />;
      }
      return <Icon name="cancel" color={Colors.accentRed()} />;
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return <Spinner purpose="body-text" />;
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return <Icon name="dot" />;
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return <Icon name="check_circle" color={Colors.accentGreen()} />;
    default:
      assertUnreachable(aggregateStatus);
  }
}

export function assetCheckExecutionStatusText(status: AssetCheckExecutionResolvedStatus): string {
  switch (status) {
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return 'Execution failed';
    case AssetCheckExecutionResolvedStatus.FAILED:
      return 'Failed';
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return 'In progress';
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return 'Skipped';
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return 'Succeeded';
    default:
      assertUnreachable(status);
  }
}

export function assetCheckExecutionStatusIcon(status: AssetCheckExecutionResolvedStatus): IconName {
  switch (status) {
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return 'sync_problem';
    case AssetCheckExecutionResolvedStatus.FAILED:
      return 'cancel';
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return 'hourglass_bottom';
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return 'dot';
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return 'check_circle';
    default:
      assertUnreachable(status);
  }
}

/**
 * Colored icon for an asset check execution status.
 * For individual execution records (e.g., historical view).
 */
export const ExecutionStatusIcon = ({
  status,
  severity,
}: {
  status: AssetCheckExecutionResolvedStatus;
  severity?: AssetCheckSeverity | null;
}) => {
  const isWarn = severity === AssetCheckSeverity.WARN;

  switch (status) {
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return <Icon name="check_circle" color={Colors.accentGreen()} size={16} />;

    case AssetCheckExecutionResolvedStatus.FAILED:
      if (isWarn) {
        return <Icon name="warning_outline" color={Colors.accentYellow()} size={16} />;
      }
      return <Icon name="cancel" color={Colors.accentRed()} size={16} />;

    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      if (isWarn) {
        return <Icon name="sync_problem" color={Colors.accentYellow()} size={16} />;
      }
      return <Icon name="sync_problem" color={Colors.accentRed()} size={16} />;

    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return <Spinner purpose="body-text" />;

    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return <Icon name="dot" size={16} />;

    default:
      assertUnreachable(status);
  }
};

export type AssetCheckIconType =
  | AssetCheckExecutionResolvedStatus
  | 'ERROR'
  | 'WARN'
  | 'NOT_EVALUATED';

export interface AssetCheckPartitionStats {
  numSucceeded: number;
  numFailed: number;
  numExecutionFailed: number;
  numInProgress: number;
  numSkipped: number;
}

type AssetCheckPartitionRangeStatus =
  | 'SUCCEEDED'
  | 'FAILED'
  | 'EXECUTION_FAILED'
  | 'IN_PROGRESS'
  | 'SKIPPED';

const EMPTY_STATS: AssetCheckPartitionStats = {
  numSucceeded: 0,
  numFailed: 0,
  numExecutionFailed: 0,
  numInProgress: 0,
  numSkipped: 0,
};

function statsForStatus(
  status: AssetCheckPartitionRangeStatus,
  count: number = 1,
): AssetCheckPartitionStats {
  switch (status) {
    case 'SUCCEEDED':
      return {...EMPTY_STATS, numSucceeded: count};
    case 'FAILED':
      return {...EMPTY_STATS, numFailed: count};
    case 'EXECUTION_FAILED':
      return {...EMPTY_STATS, numExecutionFailed: count};
    case 'IN_PROGRESS':
      return {...EMPTY_STATS, numInProgress: count};
    case 'SKIPPED':
      return {...EMPTY_STATS, numSkipped: count};
  }
}

function mergeStats(
  a: AssetCheckPartitionStats,
  b: AssetCheckPartitionStats,
): AssetCheckPartitionStats {
  return {
    numSucceeded: a.numSucceeded + b.numSucceeded,
    numFailed: a.numFailed + b.numFailed,
    numExecutionFailed: a.numExecutionFailed + b.numExecutionFailed,
    numInProgress: a.numInProgress + b.numInProgress,
    numSkipped: a.numSkipped + b.numSkipped,
  };
}

function statsFromDefaultPartitions(
  statuses: Extract<
    NonNullable<AssetCheckWithPartitionStatuses['partitionStatuses']>,
    {__typename: 'AssetCheckDefaultPartitionStatuses'}
  >,
): AssetCheckPartitionStats {
  return {
    numSucceeded: statuses.succeededPartitions?.length || 0,
    numFailed: statuses.failedPartitions?.length || 0,
    numExecutionFailed: statuses.executionFailedPartitions?.length || 0,
    numInProgress: statuses.inProgressPartitions?.length || 0,
    numSkipped: statuses.skippedPartitions?.length || 0,
  };
}

/**
 * Calculate aggregate partition statistics for a check.
 * Returns null if the check is not partitioned.
 */
export function getCheckPartitionStats(
  check: AssetCheckWithPartitionStatuses,
): AssetCheckPartitionStats | null {
  if (!check.partitionStatuses) {
    return null;
  }

  const statuses = check.partitionStatuses;
  let stats: AssetCheckPartitionStats;

  if (statuses.__typename === 'AssetCheckDefaultPartitionStatuses') {
    stats = statsFromDefaultPartitions(statuses);
  } else if (statuses.__typename === 'AssetCheckTimePartitionStatuses') {
    stats = (statuses.ranges ?? []).reduce(
      (acc, range) => mergeStats(acc, statsForStatus(range.status, 1)),
      EMPTY_STATS,
    );
  } else if (statuses.__typename === 'AssetCheckMultiPartitionStatuses') {
    stats = (statuses.ranges ?? []).reduce((acc, range) => {
      const secondaryDim = range.secondaryDim;
      if (secondaryDim.__typename === 'AssetCheckDefaultPartitionStatuses') {
        return mergeStats(acc, statsFromDefaultPartitions(secondaryDim));
      } else if (secondaryDim.__typename === 'AssetCheckTimePartitionStatuses') {
        return (secondaryDim.ranges ?? []).reduce(
          (innerAcc, r) => mergeStats(innerAcc, statsForStatus(r.status, 1)),
          acc,
        );
      }
      return acc;
    }, EMPTY_STATS);
  } else {
    return null;
  }

  // If all counts are zero, the check is not actually partitioned (empty arrays)
  // Return null to fall back to single execution behavior
  const totalPartitions =
    stats.numSucceeded +
    stats.numFailed +
    stats.numExecutionFailed +
    stats.numInProgress +
    stats.numSkipped;

  if (totalPartitions === 0) {
    return null;
  }

  return stats;
}

/**
 * Get aggregate icon type for a check (handles partitioned checks).
 * Follows priority: ERROR > WARN > IN_PROGRESS > SKIPPED > SUCCEEDED > NOT_EVALUATED
 */
export function getAggregateCheckIconType(
  check: AssetCheckWithPartitionStatuses,
): AssetCheckIconType {
  const partitionStats = getCheckPartitionStats(check);

  if (!partitionStats) {
    // Fall back to single execution behavior
    const status = check.executionForLatestMaterialization?.status;
    return status === undefined
      ? 'NOT_EVALUATED'
      : status === AssetCheckExecutionResolvedStatus.FAILED
        ? check.executionForLatestMaterialization?.evaluation?.severity === AssetCheckSeverity.WARN
          ? 'WARN'
          : 'ERROR'
        : status === AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
          ? 'ERROR'
          : status;
  }

  // Apply aggregation logic: ANY failed → FAILED
  if (partitionStats.numFailed > 0 || partitionStats.numExecutionFailed > 0) {
    // Check severity to distinguish WARN from ERROR
    const severity = check.executionForLatestMaterialization?.evaluation?.severity;
    return severity === AssetCheckSeverity.WARN ? 'WARN' : 'ERROR';
  }

  if (partitionStats.numInProgress > 0) {
    return AssetCheckExecutionResolvedStatus.IN_PROGRESS;
  }

  if (partitionStats.numSkipped > 0) {
    return AssetCheckExecutionResolvedStatus.SKIPPED;
  }

  if (partitionStats.numSucceeded > 0) {
    return AssetCheckExecutionResolvedStatus.SUCCEEDED;
  }

  return 'NOT_EVALUATED';
}
