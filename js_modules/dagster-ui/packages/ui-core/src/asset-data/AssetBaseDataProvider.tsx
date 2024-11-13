import React from 'react';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
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
      const {data} = await client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
        query: ASSETS_GRAPH_LIVE_QUERY,
        fetchPolicy: 'no-cache',
        variables: {
          assetKeys: keys.map(tokenToAssetKey),
        },
      });

      const nodesByKey = Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );

      return Object.fromEntries(
        data.assetsLatestInfo
          .map((assetLatestInfo) => {
            const id = tokenForAssetKey(assetLatestInfo.assetKey);
            const node = nodesByKey[id];
            return node ? [id, buildLiveDataForNode(node, assetLatestInfo)] : null;
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
    freshnessInfo {
      ...AssetNodeLiveFreshnessInfo
    }
    partitionStats {
      numMaterialized
      numMaterializing
      numPartitions
      numFailed
    }
  }

  fragment AssetNodeLiveFreshnessInfo on AssetFreshnessInfo {
    currentMinutesLate
  }

  fragment AssetNodeLiveMaterialization on MaterializationEvent {
    timestamp
    runId
  }

  fragment AssetNodeLiveObservation on ObservationEvent {
    timestamp
    runId
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

// For tests
export function __resetForJest() {
  Object.assign(AssetBaseData, init());
}
