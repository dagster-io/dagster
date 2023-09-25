import {ApolloClient, useApolloClient} from '@apollo/client';
import React from 'react';

import {assertUnreachable} from '../app/Util';
import {LiveDataForNode, buildLiveDataForNode} from '../asset-graph/Utils';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetLatestInfoFragment,
  AssetNodeLiveFragment,
} from '../asset-graph/types/useLiveDataForAssetKeys.types';
import {
  ASSETS_GRAPH_LIVE_QUERY,
  ASSET_LATEST_INFO_FRAGMENT,
  ASSET_NODE_LIVE_FRAGMENT,
} from '../asset-graph/useLiveDataForAssetKeys';
import {AssetKeyInput} from '../graphql/types';
import {isDocumentVisible, useDocumentVisibility} from '../hooks/useDocumentVisibility';

const _assetKeyListeners: Record<string, Array<DataForNodeListener>> = {};

export function useAssetNodeLiveData(assetKeys: AssetKeyInput[]) {
  const context = React.useContext(AssetLiveDataContext);
  return context.useAssetNodeLiveData(assetKeys);
}

function _getAssetFromCache(client: ApolloClient<any>, uniqueId: string) {
  const cachedAssetData = client.readFragment<AssetNodeLiveFragment>({
    fragment: ASSET_NODE_LIVE_FRAGMENT,
    fragmentName: 'AssetNodeLiveFragment',
    id: `assetNodeLiveFragment-${uniqueId}`,
  });
  const cachedLatestInfo = client.readFragment<AssetLatestInfoFragment>({
    fragment: ASSET_LATEST_INFO_FRAGMENT,
    fragmentName: 'AssetLatestInfoFragment',
    id: `assetLatestInfoFragment-${uniqueId}`,
  });
  if (cachedAssetData && cachedLatestInfo) {
    return {cachedAssetData, cachedLatestInfo};
  } else {
    return null;
  }
}

async function _queryAssetKeys(client: ApolloClient<any>, assetKeys: AssetKeyInput[]) {
  const {data} = await client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    fetchPolicy: 'network-only',
    variables: {
      assetKeys,
    },
  });
  data.assetNodes.forEach((assetNode) => {
    _assetKeyToUniqueId[JSON.stringify(assetNode.assetKey.path)] = assetNode.id;
    client.writeFragment({
      fragment: ASSET_NODE_LIVE_FRAGMENT,
      fragmentName: 'AssetNodeLiveFragment',
      id: `assetNodeLiveFragment-${assetNode.id}`,
      data: assetNode,
    });
  });
  data.assetsLatestInfo.forEach((assetLatestInfo) => {
    _assetKeyToUniqueId[JSON.stringify(assetLatestInfo.assetKey.path)] = assetLatestInfo.id;
    client.writeFragment({
      fragment: ASSET_LATEST_INFO_FRAGMENT,
      fragmentName: 'AssetLatestInfoFragment',
      id: `assetLatestInfoFragment-${assetLatestInfo.id}`,
      data: assetLatestInfo,
    });
  });
}

// How many assets to fetch at once
const BATCH_SIZE = 50;

// Milliseconds we wait until sending a batched query
const BATCHING_INTERVAL = 100;

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
// const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

type DataForNodeListener = (stringKey: string, data: LiveDataForNode) => void;

const AssetLiveDataContext = React.createContext<{
  useAssetNodeLiveData: (keys: AssetKeyInput[]) => Record<string, LiveDataForNode | null>;
}>({
  useAssetNodeLiveData: () => ({}),
});

// Map of asset keys to their last fetched time and last requested time
const lastFetchedOrRequested: Record<
  string,
  {fetched: number; requested?: undefined} | {requested: number; fetched?: undefined} | null
> = {};

export const AssetLiveDataProvider = ({children}: {children: React.ReactNode}) => {
  const [needsImmediateFetch, setNeedsImmediateFetch] = React.useState<boolean>(false);

  const client = useApolloClient();

  function useAssetNodeLiveData(assetKeys: AssetKeyInput[]) {
    const [data, setData] = React.useState<Record<string, LiveDataForNode | null>>({});

    React.useEffect(() => {
      const setDataSingle = (stringKey: string, assetData: LiveDataForNode) => {
        setData((data) => {
          return {...data, [stringKey]: assetData};
        });
      };
      assetKeys.forEach((key) => {
        _subscribeToAssetKey(client, key, setDataSingle, setNeedsImmediateFetch);
      });
      return () => {
        assetKeys.forEach((key) => {
          _unsubscribeToAssetKey(key, setDataSingle);
        });
      };
    }, [assetKeys]);

    return data;
  }

  const isDocumentVisible = useDocumentVisibility();

  React.useEffect(() => {
    if (!isDocumentVisible) {
      return;
    }
    // Check for assets to fetch every 5 seconds to simplify logic
    // This means assets will be fetched at most 5 + SUBSCRIPTION_IDLE_POLL_RATE after their first fetch
    // but then will be fetched every SUBSCRIPTION_IDLE_POLL_RATE after that
    const interval = setInterval(() => fetchData(client), 5000);
    fetchData(client);
    return () => {
      clearInterval(interval);
    };
  }, [client, isDocumentVisible]);

  React.useEffect(() => {
    if (!needsImmediateFetch) {
      return;
    }
    const timeout = setTimeout(() => {
      fetchData(client);
      setNeedsImmediateFetch(false);
      // Wait BATCHING_INTERVAL before doing fetch in case the component is unmounted quickly (eg. in the case of scrolling/filtering quickly)
    }, BATCHING_INTERVAL);
    return () => {
      clearTimeout(timeout);
    };
  }, [client, needsImmediateFetch]);

  return (
    <AssetLiveDataContext.Provider value={{useAssetNodeLiveData}}>
      {children}
    </AssetLiveDataContext.Provider>
  );
};

let isFetching = false;
async function _batchedQueryAssets(
  assetKeys: AssetKeyInput[],
  client: ApolloClient<any>,
  setData: (data: Record<string, LiveDataForNode>) => void,
) {
  // Bail if the document isn't visible
  if (!assetKeys.length || isFetching) {
    return;
  }
  isFetching = true;
  // Use Date.now because it properly advances in jest with fakeTimers /shrug
  const requestTime = Date.now();
  assetKeys.forEach((key) => {
    lastFetchedOrRequested[JSON.stringify(key.path)] = {
      requested: requestTime,
    };
  });
  await _queryAssetKeys(client, assetKeys);
  const data: Record<string, LiveDataForNode> = {};
  assetKeys.forEach((key) => {
    const stringKey = JSON.stringify(key.path);
    const uniqueId = _assetKeyToUniqueId[stringKey];
    if (!uniqueId) {
      assertUnreachable(
        `Expected uniqueID for assetKey to be known after fetching it's data: ${stringKey}` as never,
      );
      return;
    }
    const cachedData = _getAssetFromCache(client, uniqueId)!;
    if (cachedData) {
      const {cachedAssetData, cachedLatestInfo} = cachedData;
      data[stringKey] = buildLiveDataForNode(cachedAssetData, cachedLatestInfo);
    } else {
      assertUnreachable(
        ('Apollo failed to populate cache for asset key: ' + JSON.stringify(key.path)) as never,
      );
    }
  });
  const fetchedTime = Date.now();
  assetKeys.forEach((key) => {
    lastFetchedOrRequested[JSON.stringify(key.path)] = {
      fetched: fetchedTime,
    };
  });
  setData(data);
  isFetching = false;
  const nextAssets = _determineAssetsToFetch();
  if (nextAssets.length) {
    _batchedQueryAssets(nextAssets, client, setData);
  }
}

function _subscribeToAssetKey(
  client: ApolloClient<any>,
  assetKey: AssetKeyInput,
  setData: DataForNodeListener,
  setNeedsImmediateFetch: (needsFetch: boolean) => void,
) {
  const stringKey = JSON.stringify(assetKey.path);
  _assetKeyListeners[stringKey] = _assetKeyListeners[stringKey] || [];
  _assetKeyListeners[stringKey]!.push(setData);
  const uniqueId = _assetKeyToUniqueId[stringKey];
  const cachedData = uniqueId ? _getAssetFromCache(client, uniqueId) : null;
  if (cachedData) {
    const {cachedAssetData, cachedLatestInfo} = cachedData;
    setData(stringKey, buildLiveDataForNode(cachedAssetData, cachedLatestInfo));
  } else {
    setNeedsImmediateFetch(true);
  }
}

function _unsubscribeToAssetKey(assetKey: AssetKeyInput, setData: DataForNodeListener) {
  const stringKey = JSON.stringify(assetKey.path);
  const listeners = _assetKeyListeners[stringKey];
  if (!listeners) {
    return;
  }
  const indexToRemove = listeners.indexOf(setData);
  listeners.splice(indexToRemove, 1);
  if (!listeners.length) {
    delete _assetKeyListeners[stringKey];
  }
}

// Determine assets to fetch taking into account the last time they were fetched and whether they are already being fetched.
function _determineAssetsToFetch() {
  const assetsToFetch: AssetKeyInput[] = [];
  const assetsWithoutData: AssetKeyInput[] = [];
  const allKeys = Object.keys(_assetKeyListeners);
  while (allKeys.length && (assetsToFetch.length < BATCH_SIZE || assetsWithoutData.length < 50)) {
    const key = allKeys.shift()!;
    const isRequested = !!lastFetchedOrRequested[key]?.requested;
    if (isRequested) {
      continue;
    }
    const lastFetchTime = lastFetchedOrRequested[key]?.fetched ?? null;
    if (lastFetchTime !== null && Date.now() - lastFetchTime < SUBSCRIPTION_IDLE_POLL_RATE) {
      continue;
    }
    if (lastFetchTime && isDocumentVisible()) {
      assetsToFetch.push({path: JSON.parse(key)});
    } else {
      assetsWithoutData.push({path: JSON.parse(key)});
    }
  }
  // Prioritize fetching assets for which there is no data in the cache
  return assetsWithoutData.concat(assetsToFetch).slice(0, 50);
}

function fetchData(client: ApolloClient<any>) {
  _batchedQueryAssets(_determineAssetsToFetch(), client, (data) => {
    Object.entries(data).forEach(([key, assetData]) => {
      const listeners = _assetKeyListeners[key];
      if (!listeners) {
        return;
      }
      listeners.forEach((listener) => {
        listener(key, assetData);
      });
    });
  });
}

// Map of AssetKeyInput to its unique asset ID. We won't know until we query because the backend implementation depends on the repository location and name.
const _assetKeyToUniqueId: Record<string, string> = {};
