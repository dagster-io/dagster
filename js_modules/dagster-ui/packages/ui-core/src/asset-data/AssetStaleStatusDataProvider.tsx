import React from 'react';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {
  AssetStaleStatusDataQuery,
  AssetStaleStatusDataQueryVariables,
} from './types/AssetStaleStatusDataProvider.types';
import {tokenForAssetKey, tokenToAssetKey} from '../asset-graph/Utils';
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
      const {data} = await client.query<
        AssetStaleStatusDataQuery,
        AssetStaleStatusDataQueryVariables
      >({
        query: ASSET_STALE_STATUS_QUERY,
        fetchPolicy: 'no-cache',
        variables: {
          assetKeys: keys.map(tokenToAssetKey),
        },
      });
      return Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );
    },
  );
}
export const AssetStaleStatusData = init();

export function useAssetStaleData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  const result = AssetStaleStatusData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetStaleData', !!result.liveData);
  return result;
}

export function useAssetsStaleData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'default',
) {
  const result = AssetStaleStatusData.useLiveData(
    React.useMemo(() => assetKeys.map((key) => tokenForAssetKey(key)), [assetKeys]),
    thread,
  );
  useBlockTraceUntilTrue(
    'useAssetsStaleData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
  );
  return result;
}

export const ASSET_STALE_STATUS_QUERY = gql`
  fragment AssetStaleDataFragment on AssetNode {
    id
    assetKey {
      path
    }
    staleStatus
    staleCauses {
      key {
        path
      }
      reason
      category
      dependency {
        path
      }
    }
  }
  query AssetStaleStatusDataQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...AssetStaleDataFragment
    }
  }
`;

// For tests
export function __resetForJest() {
  Object.assign(AssetStaleStatusData, init());
}
