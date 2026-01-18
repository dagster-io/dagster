import React from 'react';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetsFreshnessInfoQuery,
  AssetsFreshnessInfoQueryVariables,
} from './types/AssetBaseDataProvider.types';
import {
  LiveDataForNode,
  buildLiveDataForNode,
  tokenForAssetKey,
  tokenToAssetKey,
} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

function init() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      const assetKeys = keys.map(tokenToAssetKey);
      const [graphResponse, freshnessResponse] = await Promise.all([
        client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
          query: ASSETS_GRAPH_LIVE_QUERY,
          fetchPolicy: 'no-cache',
          variables: {
            assetKeys,
          },
        }),
        client.query<AssetsFreshnessInfoQuery, AssetsFreshnessInfoQueryVariables>({
          query: ASSETS_FRESHNESS_INFO_QUERY,
          fetchPolicy: 'no-cache',
          variables: {
            assetKeys,
          },
        }),
      ]);

      const {data} = graphResponse;
      const {data: freshnessData} = freshnessResponse;

      const nodesByKey = Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );

      const freshnessInfoByKey = Object.fromEntries(
        freshnessData.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );

      return Object.fromEntries(
        data.assetsLatestInfo
          .map((assetLatestInfo) => {
            const id = tokenForAssetKey(assetLatestInfo.assetKey);
            const node = nodesByKey[id];
            const freshnessInfo = freshnessInfoByKey[id];
            return node
              ? [
                  id,
                  buildLiveDataForNode(
                    {
                      ...node,
                      ...(freshnessInfo ?? {
                        freshnessInfo: null,
                      }),
                    },
                    assetLatestInfo,
                  ),
                ]
              : null;
          })
          .filter((entry): entry is [string, LiveDataForNode] => !!entry),
      );
    },
  );
}
export const AssetBaseData = init();

export function useAssetBaseData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  const result = AssetBaseData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetStaleData', !!result.liveData);
  return result;
}

export function useAssetsBaseData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'default',
) {
  const result = AssetBaseData.useLiveData(
    React.useMemo(() => assetKeys.map((key) => tokenForAssetKey(key)), [assetKeys]),
    thread,
  );
  useBlockTraceUntilTrue(
    'useAssetsBaseData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
  );
  return result;
}

export function AssetBaseDataRefreshButton() {
  return <AssetBaseData.LiveDataRefresh />;
}

export const ASSET_LATEST_INFO_FRAGMENT = gql`
  fragment AssetLatestInfoFragment on AssetLatestInfo {
    id
    assetKey {
      path
    }
    unstartedRunIds
    inProgressRunIds
    latestRun {
      id
      ...AssetLatestInfoRun
    }
  }

  fragment AssetLatestInfoRun on Run {
    status
    startTime
    endTime
    id
  }
`;

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opNames
    repository {
      id
    }
    assetKey {
      path
    }
    assetMaterializations(limit: 1) {
      ...AssetNodeLiveMaterialization
    }
    assetObservations(limit: 1) {
      ...AssetNodeLiveObservation
    }
    assetChecksOrError {
      ... on AssetChecks {
        checks {
          ...AssetCheckLiveFragment
        }
      }
    }
    partitionStats {
      numMaterialized
      numMaterializing
      numPartitions
      numFailed
    }
  }

  fragment AssetNodeLiveMaterialization on MaterializationEvent {
    timestamp
    runId
    stepKey
  }

  fragment AssetNodeLiveObservation on ObservationEvent {
    timestamp
    runId
    stepKey
  }

  fragment AssetCheckLiveFragment on AssetCheck {
    name
    canExecuteIndividually
    executionForLatestMaterialization {
      id
      runId
      status
      timestamp
      stepKey
      evaluation {
        severity
      }
    }
  }
`;

export const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
    assetsLatestInfo(assetKeys: $assetKeys) {
      id
      ...AssetLatestInfoFragment
    }
  }

  ${ASSET_NODE_LIVE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;

export const ASSETS_FRESHNESS_INFO_QUERY = gql`
  query AssetsFreshnessInfoQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      assetKey {
        path
      }
      freshnessInfo {
        ...AssetNodeLiveFreshnessInfoFragment
      }
    }
  }

  fragment AssetNodeLiveFreshnessInfoFragment on AssetFreshnessInfo {
    currentMinutesLate
  }
`;

// For tests
export function __resetForJest() {
  Object.assign(AssetBaseData, init());
}
