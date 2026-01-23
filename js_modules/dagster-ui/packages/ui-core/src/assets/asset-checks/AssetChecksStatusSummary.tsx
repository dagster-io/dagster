import {
  Box,
  Colors,
  Icon,
  Intent,
  Popover,
  Spinner,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import countBy from 'lodash/countBy';
import * as React from 'react';

import {CheckStatusRow} from './AssetCheckStatusTag';
import {AssetCheckIconType, getAggregateCheckIconType} from './util';
import {assertUnreachable} from '../../app/Util';
import {AssetCheckLiveFragment} from '../../asset-data/types/AssetBaseDataProvider.types';
import {LiveDataForNode} from '../../asset-graph/Utils';
import {AssetCheckExecutionResolvedStatus, AssetKeyInput} from '../../graphql/types';

const AssetCheckIconsOrdered: {
  type: AssetCheckIconType;
  content: React.ReactNode;
  intent: Intent;
}[] = [
  {
    type: AssetCheckExecutionResolvedStatus.IN_PROGRESS,
    content: <Spinner purpose="caption-text" />,
    intent: 'none',
  },
  {
    type: 'NOT_EVALUATED',
    content: <Icon name="dot" color={Colors.accentGray()} />,
    intent: 'none',
  },
  {
    type: 'ERROR',
    content: <Icon name="cancel" color={Colors.accentRed()} />,
    intent: 'danger',
  },
  {
    type: 'WARN',
    content: <Icon name="warning_outline" color={Colors.accentYellow()} />,
    intent: 'warning',
  },
  {
    type: AssetCheckExecutionResolvedStatus.SKIPPED,
    content: <Icon name="dot" color={Colors.accentGray()} />,
    intent: 'none',
  },
  {
    type: AssetCheckExecutionResolvedStatus.SUCCEEDED,
    content: <Icon name="check_circle" color={Colors.accentGreen()} />,
    intent: 'success',
  },
];

const titlePerCheckType = (type: AssetCheckIconType) => {
  switch (type) {
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return 'In progress';
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return 'Skipped';
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return 'Succeeded';
    case AssetCheckExecutionResolvedStatus.FAILED:
      return 'Failed';
    case AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
      return 'Execution failed';
    case 'NOT_EVALUATED':
      return 'Not evaluated';
    case 'WARN':
      return 'Failed';
    case 'ERROR':
      return 'Failed';
    default:
      assertUnreachable(type);
  }
};

export const ChecksSummaryPopover = ({
  type,
  assetKey,
  assetChecks,
  useLatestStatus = false,
}: {
  type: AssetCheckIconType;
  assetKey: AssetKeyInput;
  assetChecks: AssetCheckLiveFragment[];
  useLatestStatus?: boolean;
}) => {
  return (
    <Box flex={{direction: 'column'}} style={{maxHeight: 300, overflowY: 'auto'}}>
      <Box padding={{horizontal: 12, vertical: 8}} border="bottom">
        <Subtitle2>{`${titlePerCheckType(type)} checks`}</Subtitle2>
      </Box>
      {assetChecks.map((check) => (
        <CheckStatusRow
          key={check.name}
          assetCheck={check}
          assetKey={assetKey}
          useLatestStatus={useLatestStatus}
        />
      ))}
    </Box>
  );
};

function iconTypeFromCheck(check: AssetCheckLiveFragment): AssetCheckIconType {
  return getAggregateCheckIconType(check);
}

function iconTypeFromLatestExecution(check: AssetCheckLiveFragment): AssetCheckIconType {
  const execution = check.executionForLatestMaterialization;
  if (!execution?.status) {
    return 'NOT_EVALUATED';
  }
  const status = execution.status;
  const isWarn = execution.evaluation?.severity === 'WARN';

  if (status === AssetCheckExecutionResolvedStatus.FAILED) {
    return isWarn ? 'WARN' : 'ERROR';
  }
  if (status === AssetCheckExecutionResolvedStatus.EXECUTION_FAILED) {
    return 'ERROR';
  }
  return status;
}

export const AssetChecksStatusSummary = ({
  liveData,
  rendering,
  assetKey,
}: {
  liveData: LiveDataForNode;
  rendering: 'dag2025' | 'dag' | 'tags';
  assetKey: AssetKeyInput;
}) => {
  // For tags rendering (Overview Tab), use latest execution status
  // For dag renderings, use aggregate status
  const iconTypeFunction = rendering === 'tags' ? iconTypeFromLatestExecution : iconTypeFromCheck;
  const byIconType = countBy(liveData.assetChecks, iconTypeFunction);

  if (rendering === 'dag2025') {
    const icon = () => {
      if (byIconType['ERROR']) {
        return <Icon name="close" color={Colors.accentRed()} />;
      }
      if (byIconType['WARN']) {
        return <Icon name="warning_outline" color={Colors.accentYellow()} />;
      }
      if (byIconType['SKIPPED']) {
        return <Icon name="dot" color={Colors.accentGray()} />;
      }
      return <Icon name="done" color={Colors.accentGreen()} />;
    };

    // Calculate total passed/total checks - count each check as 1 unit
    const {passed, total} = liveData.assetChecks.reduce(
      (acc, check) => {
        // Count each check as 1 unit, regardless of partitioning
        const aggregateStatus = getAggregateCheckIconType(check);

        if (aggregateStatus === AssetCheckExecutionResolvedStatus.SUCCEEDED) {
          acc.passed += 1;
        }
        acc.total += 1;

        return acc;
      },
      {passed: 0, total: 0},
    );

    return (
      <Box flex={{gap: 4, alignItems: 'center'}}>
        {icon()}
        <span>
          {passed} / {total} Passed
        </span>
      </Box>
    );
  }
  if (rendering === 'dag') {
    return (
      <Box flex={{gap: 6, alignItems: 'center'}}>
        {AssetCheckIconsOrdered.filter((a) => byIconType[a.type]).map(({content, type}) => (
          <Box flex={{gap: 2, alignItems: 'center'}} key={type}>
            {content}
            {byIconType[type]}
          </Box>
        ))}
      </Box>
    );
  }
  return (
    <Box flex={{gap: 2, alignItems: 'center'}}>
      {AssetCheckIconsOrdered.filter((a) => byIconType[a.type]).map(({content, type, intent}) => (
        <Popover
          key={type}
          content={
            <ChecksSummaryPopover
              type={type}
              assetKey={assetKey}
              assetChecks={liveData.assetChecks.filter((a) => iconTypeFunction(a) === type)}
              useLatestStatus={rendering === 'tags'}
            />
          }
          position="top-left"
          interactionKind="hover"
          className="chunk-popover-target"
        >
          <Tag intent={intent}>
            <Box flex={{gap: 2, alignItems: 'center'}}>
              {content}
              {byIconType[type]}
            </Box>
          </Tag>
        </Popover>
      ))}
    </Box>
  );
};
