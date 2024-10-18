import {
  Box,
  Colors,
  Icon,
  Popover,
  Spinner,
  Subtitle2,
  Tag,
  TagIntent,
} from '@dagster-io/ui-components';
import countBy from 'lodash/countBy';
import * as React from 'react';

import {CheckStatusRow} from './AssetCheckStatusTag';
import {assertUnreachable} from '../../app/Util';
import {AssetCheckLiveFragment} from '../../asset-data/types/AssetBaseDataProvider.types';
import {LiveDataForNode} from '../../asset-graph/Utils';
import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  AssetKeyInput,
} from '../../graphql/types';

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

const titlePerCheckType = (type: AssetCheckIconType) => {
  switch (type) {
    case AssetCheckExecutionResolvedStatus.IN_PROGRESS:
      return 'In progress';
    case AssetCheckExecutionResolvedStatus.SKIPPED:
      return 'Skipped';
    case AssetCheckExecutionResolvedStatus.SUCCEEDED:
      return 'Succeeded';
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
}: {
  type: AssetCheckIconType;
  assetKey: AssetKeyInput;
  assetChecks: AssetCheckLiveFragment[];
}) => {
  return (
    <Box flex={{direction: 'column'}} style={{maxHeight: 300, overflowY: 'auto'}}>
      <Box padding={{horizontal: 12, vertical: 8}} border="bottom">
        <Subtitle2>{`${titlePerCheckType(type)} checks`}</Subtitle2>
      </Box>
      {assetChecks.map((check) => (
        <CheckStatusRow key={check.name} assetCheck={check} assetKey={assetKey} />
      ))}
    </Box>
  );
};

function iconTypeFromCheck(check: AssetCheckLiveFragment): AssetCheckIconType {
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

export const AssetChecksStatusSummary = ({
  liveData,
  rendering,
  assetKey,
}: {
  liveData: LiveDataForNode;
  rendering: 'dag' | 'tags';
  assetKey: AssetKeyInput;
}) => {
  const byIconType = countBy(liveData.assetChecks, iconTypeFromCheck);

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
        <Popover
          key={type}
          content={
            <ChecksSummaryPopover
              type={type}
              assetKey={assetKey}
              assetChecks={liveData.assetChecks.filter((a) => iconTypeFromCheck(a) === type)}
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
