import {
  BaseTag,
  Box,
  Colors,
  Icon,
  MiddleTruncate,
  Popover,
  Spinner,
  Tag,
  intentToFillColor,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {ChecksSummaryPopover} from './AssetChecksStatusSummary';
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
}: {
  assetCheck: AssetCheckLiveFragment;
  assetKey: AssetKeyInput;
}) => {
  const {executionForLatestMaterialization: execution} = assetCheck;

  // Note: this uses BaseTag for a "grayer" style than the default tag intent
  if (!execution) {
    return (
      <CheckRow
        icon={<Icon name="status" color={Colors.accentGray()} />}
        checkName={assetCheck.name}
        assetKey={assetKey}
      />
    );
  }

  const {status, timestamp, evaluation} = execution;
  if (!status) {
    return null;
  }

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
      return (
        <CheckRow
          icon={
            isWarn ? (
              <Icon name="warning_outline" color={intentToFillColor('warning')} />
            ) : (
              <Icon name="cancel" color={intentToFillColor('danger')} />
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
              <Icon name="changes_present" color={intentToFillColor('warning')} />
            ) : (
              <Icon name="changes_present" color={intentToFillColor('danger')} />
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
          icon={<Icon name="check_circle" color={intentToFillColor('success')} />}
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
}: {
  execution:
    | (Pick<AssetCheckExecution, 'runId' | 'status' | 'timestamp' | 'stepKey'> & {
        evaluation: Pick<AssetCheckEvaluation, 'severity'> | null;
      })
    | null;
}) => {
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
      {renderTag()}
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
    const execution = checks[0]!.executionForLatestMaterialization;

    actions.push({
      label: 'View details',
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
