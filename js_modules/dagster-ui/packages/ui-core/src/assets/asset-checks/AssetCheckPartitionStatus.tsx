import {Colors} from '@dagster-io/ui-components';
import {CSSProperties} from 'react';

import {assertUnreachable} from '../../app/Util';
import {AssetCheckExecutionResolvedStatus} from '../../graphql/types';

// Asset Check Partition Status includes all execution statuses plus MISSING for unattempted partitions
export enum AssetCheckPartitionStatus {
  MISSING = 'MISSING',
  IN_PROGRESS = 'IN_PROGRESS',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED',
  EXECUTION_FAILED = 'EXECUTION_FAILED',
  SKIPPED = 'SKIPPED',
}

export const emptyAssetCheckPartitionStatusCounts = () => ({
  [AssetCheckPartitionStatus.MISSING]: 0,
  [AssetCheckPartitionStatus.IN_PROGRESS]: 0,
  [AssetCheckPartitionStatus.SUCCEEDED]: 0,
  [AssetCheckPartitionStatus.FAILED]: 0,
  [AssetCheckPartitionStatus.EXECUTION_FAILED]: 0,
  [AssetCheckPartitionStatus.SKIPPED]: 0,
});

export const assetCheckPartitionStatusToText = (status: AssetCheckPartitionStatus) => {
  switch (status) {
    case AssetCheckPartitionStatus.MISSING:
      return 'Missing';
    case AssetCheckPartitionStatus.SUCCEEDED:
      return 'Passed';
    case AssetCheckPartitionStatus.IN_PROGRESS:
      return 'In Progress';
    case AssetCheckPartitionStatus.FAILED:
      return 'Failed';
    case AssetCheckPartitionStatus.EXECUTION_FAILED:
      return 'Execution Failed';
    case AssetCheckPartitionStatus.SKIPPED:
      return 'Skipped';
    default:
      assertUnreachable(status);
  }
};

const assetCheckPartitionStatusToColor = (status: AssetCheckPartitionStatus) => {
  switch (status) {
    case AssetCheckPartitionStatus.MISSING:
      return Colors.accentGray();
    case AssetCheckPartitionStatus.SUCCEEDED:
      return Colors.accentGreen();
    case AssetCheckPartitionStatus.IN_PROGRESS:
      return Colors.accentBlue();
    case AssetCheckPartitionStatus.FAILED:
    case AssetCheckPartitionStatus.EXECUTION_FAILED:
      return Colors.accentRed();
    case AssetCheckPartitionStatus.SKIPPED:
      return Colors.accentYellow();
    default:
      assertUnreachable(status);
  }
};

export function assetCheckPartitionStatusesToStyle(
  statuses: AssetCheckPartitionStatus[],
): CSSProperties {
  if (statuses.length === 1) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return {backgroundColor: assetCheckPartitionStatusToColor(statuses[0]!)};
  }
  const colors = statuses.map(assetCheckPartitionStatusToColor);
  const pct = 100 / colors.length;
  const stops = colors.map((c, idx) => `${c} ${idx * pct}%, ${c} ${(idx + 1) * pct}%`);
  return {
    background: `linear-gradient(to right, ${stops.join(', ')})`,
  };
}

// Helper function to convert AssetCheckExecutionResolvedStatus to AssetCheckPartitionStatus
export function executionStatusToPartitionStatus(
  status: AssetCheckExecutionResolvedStatus,
): AssetCheckPartitionStatus {
  switch (status) {
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return AssetCheckPartitionStatus.IN_PROGRESS;
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return AssetCheckPartitionStatus.SUCCEEDED;
    case AssetCheckExecutionResolvedStatus.FAILED:
      return AssetCheckPartitionStatus.FAILED;
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return AssetCheckPartitionStatus.EXECUTION_FAILED;
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return AssetCheckPartitionStatus.SKIPPED;
    default:
      assertUnreachable(status);
  }
}

// Legacy exports for backward compatibility
export const assetCheckExecutionStatusToText = assetCheckPartitionStatusToText;
export const assetCheckExecutionStatusesToStyle = assetCheckPartitionStatusesToStyle;
