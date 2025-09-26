import {Colors, Icon, Spinner} from '@dagster-io/ui-components';

import {ExecuteChecksButtonCheckFragment} from './types/ExecuteChecksButton.types';
import {AssetCheckTableFragment} from './types/VirtualizedAssetCheckTable.types';
import {assertUnreachable} from '../../app/Util';
import {
  AssetCheckExecution,
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
} from '../../graphql/types';
import {linkToRunEvent} from '../../runs/RunUtils';

export function assetCheckStatusDescription(
  check: AssetCheckTableFragment & ExecuteChecksButtonCheckFragment,
) {
  const lastExecution = check.executionForLatestMaterialization;
  if (!lastExecution) {
    return 'Not evaluated';
  }
  const status = lastExecution.status;
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

export function getCheckIcon(
  check: AssetCheckTableFragment & ExecuteChecksButtonCheckFragment,
): React.ReactNode {
  const lastExecution = check.executionForLatestMaterialization;
  if (!lastExecution) {
    return <Icon name="status" color={Colors.accentGray()} />;
  }
  const status = lastExecution.status;
  const isWarning = lastExecution.evaluation?.severity === AssetCheckSeverity.WARN;
  switch (status) {
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return (
        <Icon name="sync_problem" color={isWarning ? Colors.accentYellow() : Colors.accentRed()} />
      );
    case AssetCheckExecutionResolvedStatus.FAILED:
      if (isWarning) {
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
      assertUnreachable(status);
  }
}

export function getCheckLogsLink(
  check: Pick<AssetCheckTableFragment, 'inAppCheck' | 'name'>,
  execution: Pick<AssetCheckExecution, 'runId' | 'timestamp' | 'stepKey'>,
) {
  return check.inAppCheck
    ? `/data-quality/${check.name}/${execution.runId}`
    : linkToRunEvent(
        {id: execution.runId},
        {stepKey: execution.stepKey, timestamp: execution.timestamp},
      );
}
