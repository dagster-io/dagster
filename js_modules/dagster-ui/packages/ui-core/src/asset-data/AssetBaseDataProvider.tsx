import React from 'react';
import {queryAndBuildAssetBaseData} from 'shared/asset-data/queryAndBuildAssetBaseData.oss';

import {useApolloClient} from '../apollo-client';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

function init() {
  return liveDataFactory(() => useApolloClient(), queryAndBuildAssetBaseData);
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

// For tests
export function __resetForJest() {
  Object.assign(AssetBaseData, init());
}
