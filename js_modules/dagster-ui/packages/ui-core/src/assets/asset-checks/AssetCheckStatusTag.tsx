import {
  BaseTag,
  Box,
  Caption,
  Colors,
  Icon,
  IconName,
  Intent,
  MiddleTruncate,
  Popover,
  Spinner,
  Tag,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {ChecksSummaryPopover} from './AssetChecksStatusSummary';
import {
  AssetCheckIconType,
  AssetCheckPartitionStats,
  getAggregateCheckIconType,
  getCheckPartitionStats,
} from './util';
import {assertUnreachable} from '../../app/Util';
import {AssetCheckLiveFragment} from '../../asset-data/types/AssetBaseDataProvider.types';
import {
  AssetCheckEvaluation,
  AssetCheckExecution,
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  AssetKeyInput,
} from '../../graphql/types';
import {linkToRunEvent} from '../../runs/RunUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {TagAction, TagActionsPopover} from '../../ui/TagActions';
import {assetDetailsPathForAssetCheck} from '../assetDetailsPathForKey';

interface StatusTagConfig {
  icon?: IconName;
  intent: Intent;
  label: string;
  showSpinner?: boolean;
  partitionText?: (stats: AssetCheckPartitionStats, total: number) => string;
}

const STATUS_TAG_CONFIG: Record<AssetCheckIconType, StatusTagConfig> = {
  ERROR: {
    icon: 'cancel',
    intent: 'danger',
    label: 'Failed',
    partitionText: (stats, total) =>
      `${stats.numFailed + stats.numExecutionFailed} of ${total} partitions failed`,
  },
  WARN: {
    icon: 'warning_outline',
    intent: 'warning',
    label: 'Failed',
    partitionText: (stats, total) =>
      `${stats.numFailed + stats.numExecutionFailed} of ${total} partitions failed`,
  },
  [AssetCheckExecutionResolvedStatus.EXECUTION_FAILED]: {
    icon: 'cancel',
    intent: 'danger',
    label: 'Failed',
    partitionText: (stats, total) =>
      `${stats.numFailed + stats.numExecutionFailed} of ${total} partitions failed`,
  },
  [AssetCheckExecutionResolvedStatus.FAILED]: {
    icon: 'cancel',
    intent: 'danger',
    label: 'Failed',
    partitionText: (stats, total) =>
      `${stats.numFailed + stats.numExecutionFailed} of ${total} partitions failed`,
  },
  [AssetCheckExecutionResolvedStatus.IN_PROGRESS]: {
    intent: 'primary',
    label: 'Running',
    showSpinner: true,
    partitionText: (stats, total) => `${stats.numInProgress} of ${total} partitions in progress`,
  },
  [AssetCheckExecutionResolvedStatus.SUCCEEDED]: {
    icon: 'check_circle',
    intent: 'success',
    label: 'Passed',
    partitionText: (stats) => `All ${stats.numSucceeded} partitions passed`,
  },
  [AssetCheckExecutionResolvedStatus.SKIPPED]: {
    icon: 'dot',
    intent: 'none',
    label: 'Skipped',
    partitionText: (stats) => `All ${stats.numSkipped} partitions skipped`,
  },
  NOT_EVALUATED: {
    intent: 'none',
    label: 'Not evaluated',
  },
};

function renderStatusTag(
  status: AssetCheckIconType,
  partitionStats?: AssetCheckPartitionStats | null,
): React.ReactNode {
  const config = STATUS_TAG_CONFIG[status];
  const totalPartitions = partitionStats
    ? partitionStats.numSucceeded +
      partitionStats.numFailed +
      partitionStats.numExecutionFailed +
      partitionStats.numInProgress +
      partitionStats.numSkipped
    : 0;

  if (status === 'NOT_EVALUATED') {
    return (
      <BaseTag
        textColor={Colors.textLight()}
        fillColor={Colors.backgroundLight()}
        icon={<Icon name="status" color={Colors.accentGray()} />}
        label={config.label}
      />
    );
  }

  const partitionSummary = partitionStats && totalPartitions > 0;

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Tag icon={config.icon} intent={config.intent}>
        {config.showSpinner && (
          <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
            <Spinner purpose="body-text" />
            {config.label}
          </Box>
        )}
        {!config.showSpinner && config.label}
      </Tag>
      {partitionSummary && config.partitionText && (
        <Caption>{config.partitionText(partitionStats, totalPartitions)}</Caption>
      )}
    </Box>
  );
}

const CheckRow = ({
  icon,
  checkName,
  timestamp,
  assetKey,
}: {
  icon: JSX.Element;
  checkName: string;
  assetKey: AssetKeyInput;
  timestamp?: number;
}) => (
  <Box
    flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12}}
    padding={{horizontal: 12, vertical: 8}}
  >
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      {icon}
      <Link
        to={assetDetailsPathForAssetCheck({assetKey, name: checkName})}
        style={{textDecoration: 'none'}}
      >
        {checkName}
      </Link>
    </Box>
    {timestamp && <TimestampDisplay timestamp={timestamp} />}
  </Box>
);

export const CheckStatusRow = ({
  assetCheck,
  assetKey,
  preferLatestStatus = false,
}: {
  assetCheck: AssetCheckLiveFragment;
  assetKey: AssetKeyInput;
  preferLatestStatus?: boolean;
}) => {
  const {executionForLatestMaterialization: execution} = assetCheck;

  // Use aggregate status by default, or latest execution status if requested
  const status = preferLatestStatus ? execution?.status : getAggregateCheckIconType(assetCheck);

  // Note: this uses BaseTag for a "grayer" style than the default tag intent
  if (!execution || status === 'NOT_EVALUATED' || !status) {
    return (
      <CheckRow
        icon={<Icon name="status" color={Colors.accentGray()} />}
        checkName={assetCheck.name}
        assetKey={assetKey}
      />
    );
  }

  const {timestamp, evaluation} = execution;
  const isWarn = evaluation?.severity === AssetCheckSeverity.WARN;

  switch (status) {
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return (
        <CheckRow
          icon={<Spinner purpose="body-text" />}
          checkName={assetCheck.name}
          timestamp={timestamp}
          assetKey={assetKey}
        />
      );
    case AssetCheckExecutionResolvedStatus.FAILED:
    case 'WARN':
    case 'ERROR':
      return (
        <CheckRow
          icon={
            isWarn || status === 'WARN' ? (
              <Icon name="warning_outline" color={Colors.accentYellow()} />
            ) : (
              <Icon name="cancel" color={Colors.accentRed()} />
            )
          }
          checkName={assetCheck.name}
          timestamp={timestamp}
          assetKey={assetKey}
        />
      );
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return (
        <CheckRow
          icon={
            isWarn ? (
              <Icon name="changes_present" color={Colors.accentYellow()} />
            ) : (
              <Icon name="changes_present" color={Colors.accentRed()} />
            )
          }
          checkName={assetCheck.name}
          timestamp={timestamp}
          assetKey={assetKey}
        />
      );
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return (
        <CheckRow
          icon={<Icon name="check_circle" color={Colors.accentGreen()} />}
          checkName={assetCheck.name}
          timestamp={timestamp}
          assetKey={assetKey}
        />
      );
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return (
        <CheckRow
          icon={<Icon name="dot" />}
          checkName={assetCheck.name}
          timestamp={timestamp}
          assetKey={assetKey}
        />
      );
    default:
      assertUnreachable(status);
  }
};

export const AssetCheckStatusTag = ({
  execution,
  check,
}: {
  execution:
    | (Pick<AssetCheckExecution, 'runId' | 'status' | 'timestamp' | 'stepKey'> & {
        evaluation: Pick<AssetCheckEvaluation, 'severity'> | null;
      })
    | null;
  check?: AssetCheckLiveFragment;
}) => {
  // Get partition stats if available
  const partitionStats = check ? getCheckPartitionStats(check) : null;

  // Note: this uses BaseTag for a "grayer" style than the default tag intent
  if (!execution) {
    return (
      <BaseTag
        textColor={Colors.textLight()}
        fillColor={Colors.backgroundLight()}
        icon={<Icon name="status" color={Colors.accentGray()} />}
        label="Not evaluated"
      />
    );
  }

  const {status, runId, evaluation} = execution;
  if (!status) {
    return null;
  }

  const renderTag = () => {
    // When check is provided, always use aggregate status
    if (check) {
      const aggregateStatus = getAggregateCheckIconType(check);
      return renderStatusTag(aggregateStatus, partitionStats);
    }

    // Fall back to execution-only rendering when no check provided
    const isWarn = evaluation?.severity === AssetCheckSeverity.WARN;
    switch (status) {
      case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
        return (
          <Tag intent="primary">
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              <Spinner purpose="body-text" />
              Running
            </Box>
          </Tag>
        );
      case AssetCheckExecutionResolvedStatus.FAILED:
        return isWarn ? (
          <Tag icon="warning_outline" intent="warning">
            Failed
          </Tag>
        ) : (
          <Tag icon="cancel" intent="danger">
            Failed
          </Tag>
        );
      case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
        return (
          <Tag intent={isWarn ? 'warning' : 'danger'} icon="changes_present">
            Execution failed
          </Tag>
        );
      case AssetCheckExecutionResolvedStatus.SUCCEEDED:
        return (
          <Tag icon="check_circle" intent="success">
            Passed
          </Tag>
        );
      case AssetCheckExecutionResolvedStatus.SKIPPED:
        return <Tag icon="dot">Skipped</Tag>;
      default:
        assertUnreachable(status);
    }
  };

  // If partitioned, show partition breakdown in tooltip
  const hasPartitionStats =
    partitionStats &&
    (partitionStats.numSucceeded > 0 ||
      partitionStats.numFailed > 0 ||
      partitionStats.numExecutionFailed > 0 ||
      partitionStats.numInProgress > 0 ||
      partitionStats.numSkipped > 0);

  const tagWithPopover =
    hasPartitionStats && partitionStats ? (
      <Popover
        content={
          <Box flex={{direction: 'column', gap: 4}} padding={{vertical: 8, horizontal: 12}}>
            {partitionStats.numSucceeded > 0 && <div>{partitionStats.numSucceeded} succeeded</div>}
            {partitionStats.numFailed > 0 && <div>{partitionStats.numFailed} failed</div>}
            {partitionStats.numExecutionFailed > 0 && (
              <div>{partitionStats.numExecutionFailed} execution failed</div>
            )}
            {partitionStats.numInProgress > 0 && (
              <div>{partitionStats.numInProgress} in progress</div>
            )}
            {partitionStats.numSkipped > 0 && <div>{partitionStats.numSkipped} skipped</div>}
          </Box>
        }
        position="top"
        interactionKind="hover"
      >
        {renderTag()}
      </Popover>
    ) : (
      renderTag()
    );

  return (
    <TagActionsPopover
      data={{key: '', value: ''}}
      actions={[
        {
          label: 'View in run logs',
          to: linkToRunEvent(
            {id: runId},
            {stepKey: execution.stepKey, timestamp: execution.timestamp},
          ),
        },
      ]}
    >
      {tagWithPopover}
    </TagActionsPopover>
  );
};

export const AssetCheckErrorsTag = ({
  checks,
  severity,
  assetKey,
}: {
  checks: AssetCheckLiveFragment[];
  severity: AssetCheckSeverity;
  assetKey: AssetKeyInput;
}) => {
  const tagIcon = severity === AssetCheckSeverity.ERROR ? 'cancel' : 'warning_outline';
  const tagIntent = severity === AssetCheckSeverity.ERROR ? 'danger' : 'warning';

  if (checks.length === 1) {
    const actions: TagAction[] = [];
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const execution = checks[0]!.executionForLatestMaterialization;

    actions.push({
      label: 'View details',
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      to: assetDetailsPathForAssetCheck({assetKey, name: checks[0]!.name}),
    });
    if (execution) {
      actions.push({
        label: 'View in run logs',
        to: linkToRunEvent(
          {id: execution.runId},
          {stepKey: execution.stepKey, timestamp: execution.timestamp},
        ),
      });
    }

    return (
      <TagActionsPopover
        data={{key: '', value: ''}}
        actions={actions}
        childrenMiddleTruncate={checks.length === 1}
      >
        <Tag icon={tagIcon} intent={tagIntent}>
          {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
          <MiddleTruncate text={checks[0]!.name} />
        </Tag>
      </TagActionsPopover>
    );
  }

  return (
    <Popover
      content={<ChecksSummaryPopover type={severity} assetKey={assetKey} assetChecks={checks} />}
      position="top-left"
      interactionKind="hover"
      className="chunk-popover-target"
    >
      <Tag icon={tagIcon} intent={tagIntent}>
        {`${checks.length} failed`}
      </Tag>
    </Popover>
  );
};
