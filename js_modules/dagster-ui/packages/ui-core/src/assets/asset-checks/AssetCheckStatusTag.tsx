import {BaseTag, Box, Colors, Icon, Spinner, Tag} from '@dagster-io/ui-components';

import {assertUnreachable} from '../../app/Util';
import {
  AssetCheckEvaluation,
  AssetCheckExecution,
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
} from '../../graphql/types';
import {linkToRunEvent} from '../../runs/RunUtils';
import {TagActionsPopover} from '../../ui/TagActions';

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
