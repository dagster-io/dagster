import {Colors, Spinner, Tooltip} from '@dagster-io/ui-components';
import React from 'react';
import styled, {keyframes} from 'styled-components';

import {StatusCase} from '../AssetNodeStatusContent';
import {GraphNode} from '../Utils';

export type FolderNodeNonAssetType =
  | {groupName: string; id: string; level: number}
  | {locationName: string; id: string; level: number};

export type FolderNodeType = FolderNodeNonAssetType | {path: string; id: string; level: number};

export type TreeNodeType = {level: number; id: string; path: string};

export function nodePathKey(node: {path: string; id: string} | {id: string}) {
  return 'path' in node ? node.path : node.id;
}

export function getDisplayName(node: GraphNode) {
  return node.assetKey.path[node.assetKey.path.length - 1]!;
}

export function StatusCaseDot({statusCase}: {statusCase: StatusCase}) {
  const type = React.useMemo(() => {
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
      case StatusCase.LATE_OR_FAILED:
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
          <Dot style={{border: `2px solid ${Colors.Gray500}`}} />
        </Tooltip>
      );
    case 'failed':
      return (
        <Tooltip content="Failed" position="top">
          <Dot style={{backgroundColor: Colors.Red500}} />
        </Tooltip>
      );
    case 'inprogress':
      return <Spinner purpose="caption-text" />;
    case 'successful':
      return <Dot style={{backgroundColor: Colors.Green500}} />;
  }
}

const pulse = keyframes`
  from {
    background-color: ${Colors.Gray100}
  }

  50% {
    background-color: ${Colors.Gray300}
  }

  to {
    background-color: ${Colors.Gray100}
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
