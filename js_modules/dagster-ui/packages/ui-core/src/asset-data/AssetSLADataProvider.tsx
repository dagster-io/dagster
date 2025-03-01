import {useMemo} from 'react';
import {getAssetSLAQueryResponse} from 'shared/asset-data/getAssetSLAQueryResponse.oss';

import {ApolloClient, useApolloClient} from '../apollo-client';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

export function init() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      return getAssetSLAQueryResponse(keys, client);
    },
  );
}

export const AssetSLAData = init();

export function useAssetSLAData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  const result = AssetSLAData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetStaleData', !!result.liveData);
  return result;
}

export function useAssetsSLAData(assetKeys: AssetKeyInput[], thread: LiveDataThreadID = 'default') {
  const result = AssetSLAData.useLiveData(
    useMemo(() => assetKeys.map((key) => tokenForAssetKey(key)), [assetKeys]),
    thread,
  );
  useBlockTraceUntilTrue(
    'useAssetsSLAData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
  );
  return result;
}

export function AssetSLADataRefreshButton() {
  return <AssetSLAData.LiveDataRefresh />;
}

// For tests
export function __resetForJest() {
  Object.assign(AssetSLAData, init());
}
