import {Box, Colors, Icon, Spinner, Tag, TagIntent} from '@dagster-io/ui-components';
import countBy from 'lodash/countBy';
import * as React from 'react';

import {LiveDataForNode} from '../../asset-graph/Utils';
import {AssetCheckExecutionResolvedStatus, AssetCheckSeverity} from '../../graphql/types';

type AssetCheckIconType =
  | Exclude<
      AssetCheckExecutionResolvedStatus,
      AssetCheckExecutionResolvedStatus.FAILED | AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
    >
  | 'NOT_EVALUATED'
  | 'WARN'
  | 'ERROR';

const AssetCheckIconsOrdered: {
  type: AssetCheckIconType;
  content: React.ReactNode;
  intent: TagIntent;
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

export const AssetChecksStatusSummary = ({
  liveData,
  rendering,
}: {
  liveData: LiveDataForNode;
  rendering: 'dag' | 'tags';
}) => {
  const byIconType = countBy(liveData.assetChecks, (c) => {
    const status = c.executionForLatestMaterialization?.status;
    const value: AssetCheckIconType =
      status === undefined
        ? 'NOT_EVALUATED'
        : status === AssetCheckExecutionResolvedStatus.FAILED
        ? c.executionForLatestMaterialization?.evaluation?.severity === AssetCheckSeverity.WARN
          ? 'WARN'
          : 'ERROR'
        : status === AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
        ? 'ERROR'
        : status;
    return value;
  });

  return rendering === 'dag' ? (
    <Box flex={{gap: 6, alignItems: 'center'}}>
      {AssetCheckIconsOrdered.filter((a) => byIconType[a.type]).map(({content, type}) => (
        <Box flex={{gap: 2, alignItems: 'center'}} key={type}>
          {content}
          {byIconType[type]}
        </Box>
      ))}
    </Box>
  ) : (
    <Box flex={{gap: 2, alignItems: 'center'}}>
      {AssetCheckIconsOrdered.filter((a) => byIconType[a.type]).map(({content, type, intent}) => (
        <Tag key={type} intent={intent}>
          <Box flex={{gap: 2, alignItems: 'center'}}>
            {content}
            {byIconType[type]}
          </Box>
        </Tag>
      ))}
    </Box>
  );
};
