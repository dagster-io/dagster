import {Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import styled, {keyframes} from 'styled-components';

import {AssetKeyInput} from '../../graphql/types';
import {StatusCase} from '../AssetNodeStatusContent';
import {GraphNode} from '../Utils';

export type FolderNodeGroupType = {
  id: string;
  level: number;
  openAlways?: boolean;
  groupNode: {
    groupName: string;
    assets: GraphNode[];

    // remove when groups-outside-code-location feature flag is shipped
    repositoryName?: string;
    repositoryLocationName?: string;
  };
};

export type FolderNodeCodeLocationType = {locationName: string; id: string; level: number};

export type FolderNodeNonAssetType = FolderNodeGroupType | FolderNodeCodeLocationType;

export type FolderNodeType = FolderNodeNonAssetType | {path: string; id: string; level: number};

export type TreeNodeType = {level: number; id: string; path: string};

export function nodePathKey(node: {path: string; id: string} | {id: string}) {
  return 'path' in node ? node.path : node.id;
}

export function getDisplayName(node: {assetKey: AssetKeyInput}) {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return node.assetKey.path[node.assetKey.path.length - 1]!;
}

export function StatusCaseDot({statusCase}: {statusCase: StatusCase}) {
  const type = useMemo(() => {
    switch (statusCase) {
      case StatusCase.LOADING:
        return 'loading' as const;
      case StatusCase.SOURCE_OBSERVING:
        return 'inprogress' as const;
      case StatusCase.SOURCE_OBSERVED:
        return 'successful' as const;
      case StatusCase.SOURCE_NEVER_OBSERVED:
        return 'missing' as const;
      case StatusCase.SOURCE_NO_STATE:
        return 'missing' as const;
      case StatusCase.MATERIALIZING:
        return 'inprogress' as const;
      case StatusCase.FAILED_MATERIALIZATION:
      case StatusCase.OVERDUE:
      case StatusCase.CHECKS_FAILED:
        return 'failed' as const;
      case StatusCase.NEVER_MATERIALIZED:
        return 'missing' as const;
      case StatusCase.MATERIALIZED:
        return 'successful' as const;
      case StatusCase.PARTITIONS_FAILED:
        return 'failed' as const;
      case StatusCase.PARTITIONS_MISSING:
        return 'missing' as const;
      case StatusCase.PARTITIONS_MATERIALIZED:
        return 'successful' as const;
    }
  }, [statusCase]);

  switch (type) {
    case 'loading':
      return <LoadingDot />;
    case 'missing':
      return (
        <Tooltip content="Missing" position="top">
          <Icon name="missing" color={Colors.accentGray()} />
        </Tooltip>
      );
    case 'failed':
      return (
        <Tooltip content="Failed" position="top">
          <Icon name="check_failed" color={Colors.accentRed()} />
        </Tooltip>
      );
    case 'inprogress':
      return <Spinner purpose="caption-text" />;
    case 'successful':
      return <Icon name="run_success" color={Colors.accentGreen()} />;
  }
}

const pulse = keyframes`
  from {
    background-color: ${Colors.accentGray()}
  }

  50% {
    background-color: ${Colors.accentGrayHover()}
  }

  to {
    background-color: ${Colors.accentGray()}
  }
`;

// 1px margin for 12px total width (matches <Spinner /> size)
const Dot = styled.div`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin: 0 1px;
`;

const LoadingDot = styled(Dot)`
  animation: ${pulse} 1s ease-out infinite;
`;
