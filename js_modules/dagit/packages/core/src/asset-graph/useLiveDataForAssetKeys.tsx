import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {AssetKeyInput, PipelineSelector} from '../types/globalTypes';

import {ASSET_NODE_LIVE_FRAGMENT} from './AssetNode';
import {buildLiveData, GraphData, REPOSITORY_LIVE_FRAGMENT} from './Utils';
import {AssetGraphLiveQuery, AssetGraphLiveQueryVariables} from './types/AssetGraphLiveQuery';

/** Fetches the last materialization, "upstream changed", and other live state
 * for the assets in the given pipeline or in the given set of asset keys (or both).
 *
 * Note: The "upstream changed" flag cascades, so it may not appear if the upstream
 * node that has changed is not in scope.
 */
export function useLiveDataForAssetKeys(
  pipelineSelector: PipelineSelector | null | undefined,
  graphData: GraphData | null,
  graphAssetKeys: AssetKeyInput[],
) {
  const liveResult = useQuery<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>(
    ASSETS_GRAPH_LIVE_QUERY,
    {
      skip: graphAssetKeys.length === 0,
      variables: {
        assetKeys: graphAssetKeys,
        repositorySelector: pipelineSelector
          ? {
              repositoryLocationName: pipelineSelector.repositoryLocationName,
              repositoryName: pipelineSelector.repositoryName,
            }
          : undefined,
      },
      notifyOnNetworkStatusChange: true,
    },
  );

  const liveDataByNode = React.useMemo(() => {
    if (!liveResult.data || !graphData) {
      return {};
    }

    const {repositoriesOrError, assetNodes: liveAssetNodes} = liveResult.data;
    const repos =
      repositoriesOrError.__typename === 'RepositoryConnection' ? repositoriesOrError.nodes : [];

    return buildLiveData(graphData, liveAssetNodes, repos);
  }, [graphData, liveResult]);

  return {
    liveResult,
    liveDataByNode,
    graphAssetKeys,
  };
}

const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery($repositorySelector: RepositorySelector, $assetKeys: [AssetKeyInput!]) {
    repositoriesOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on RepositoryConnection {
        nodes {
          __typename
          id
          ...RepositoryLiveFragment
        }
      }
    }
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
  }
  ${REPOSITORY_LIVE_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;
