import {gql} from '@apollo/client';
import {Box, Icon, Mono} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {UnderlyingOpsAssetNodeFragment} from './types/UnderlyingOpsOrGraph.types';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const UnderlyingOpsOrGraph = ({
  assetNode,
  repoAddress,
  minimal,
}: {
  assetNode: UnderlyingOpsAssetNodeFragment;
  repoAddress: RepoAddress;
  minimal?: boolean;
}) => {
  const {assetKey, graphName, opNames, jobNames} = assetNode;
  const opCount = opNames.length;

  if (!opCount) {
    return null;
  }

  if (!graphName) {
    const firstOp = opNames[0];
    if (displayNameForAssetKey(assetKey) === firstOp) {
      return null;
    }
    const opPath = workspacePathFromAddress(repoAddress, `/ops/${firstOp}`);
    return (
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <Icon name="op" size={16} />
        <Mono>
          <Link to={opPath}>{firstOp}</Link>
        </Mono>
      </Box>
    );
  }

  if (!jobNames.length) {
    return null;
  }

  return (
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <Icon name="schema" size={16} />
      {minimal ? (
        <Link to={workspacePathFromAddress(repoAddress, `/graphs/${jobNames[0]}/${graphName}/`)}>
          View graph
        </Link>
      ) : (
        <Mono>
          <Link to={workspacePathFromAddress(repoAddress, `/graphs/${jobNames[0]}/${graphName}/`)}>
            {graphName}
          </Link>
          {` (${opCount === 1 ? '1 op' : `${opCount} ops`})`}
        </Mono>
      )}
    </Box>
  );
};

export const UNDERLYING_OPS_ASSET_NODE_FRAGMENT = gql`
  fragment UnderlyingOpsAssetNodeFragment on AssetNode {
    id
    assetKey {
      path
    }
    graphName
    opNames
    jobNames
  }
`;
