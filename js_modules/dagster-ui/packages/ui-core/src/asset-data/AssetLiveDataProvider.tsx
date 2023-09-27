import {ApolloClient, useApolloClient} from '@apollo/client';
import uniq from 'lodash/uniq';
import React from 'react';

import {observeAssetEventsInRuns} from '../asset-graph/AssetRunLogObserver';
import {LiveDataForNode, buildLiveDataForNode, tokenForAssetKey} from '../asset-graph/Utils';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetNodeLiveFragment,
} from '../asset-graph/types/useLiveDataForAssetKeys.types';
import {ASSETS_GRAPH_LIVE_QUERY} from '../asset-graph/useLiveDataForAssetKeys';
import {AssetKeyInput} from '../graphql/types';
import {isDocumentVisible, useDocumentVisibility} from '../hooks/useDocumentVisibility';
import {useDidLaunchEvent} from '../runs/RunUtils';

const _assetKeyListeners: Record<string, Array<DataForNodeListener>> = {};
let providerListener = (_key: string, _data: LiveDataForNode) => {};
const _cache: Record<string, LiveDataForNode> = {};

/*
 * Note: This hook may return partial data since it will fetch assets in chunks/batches.
 */
export function useAssetsLiveData(assetKeys: AssetKeyInput[]) {
  const [data, setData] = React.useState<Record<string, LiveDataForNode>>({});
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const {setNeedsImmediateFetch, onSubscribed, onUnsubscribed} =
    React.useContext(AssetLiveDataContext);

  React.useEffect(() => {
    const setDataSingle = (stringKey: string, assetData: LiveDataForNode) => {
      setData((data) => {
        return {...data, [stringKey]: assetData};
      });
    };
    assetKeys.forEach((key) => {
      _subscribeToAssetKey(key, setDataSingle, setNeedsImmediateFetch);
    });
    onSubscribed();
    return () => {
      assetKeys.forEach((key) => {
        _unsubscribeToAssetKey(key, setDataSingle);
      });
      onUnsubscribed();
    };
  }, [assetKeys, onSubscribed, onUnsubscribed, setNeedsImmediateFetch]);

  return {
    liveDataByNode: data,
    refresh: React.useCallback(() => {
      _resetLastFetchedOrRequested(assetKeys);
      setNeedsImmediateFetch();
      setIsRefreshing(true);
    }, [setNeedsImmediateFetch, assetKeys]),
    refreshing: React.useMemo(() => {
      for (const key of assetKeys) {
        const stringKey = JSON.stringify(key.path);
        if (!lastFetchedOrRequested[stringKey]?.fetched) {
          return true;
        }
      }
      setTimeout(() => {
        setIsRefreshing(false);
      });
      return false;
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [assetKeys, data, isRefreshing]),
  };
}

async function _queryAssetKeys(client: ApolloClient<any>, assetKeys: AssetKeyInput[]) {
  const {data} = await client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    fetchPolicy: 'network-only',
    variables: {
      assetKeys,
    },
  });
  const nodesByKey: Record<string, AssetNodeLiveFragment> = {};
  const liveDataByKey: Record<string, LiveDataForNode> = {};
  data.assetNodes.forEach((assetNode) => {
    const id = JSON.stringify(assetNode.assetKey.path);
    nodesByKey[id] = assetNode;
  });
  data.assetsLatestInfo.forEach((assetLatestInfo) => {
    const id = JSON.stringify(assetLatestInfo.assetKey.path);
    liveDataByKey[id] = buildLiveDataForNode(nodesByKey[id]!, assetLatestInfo);
  });
  Object.assign(_cache, liveDataByKey);
  return liveDataByKey;
}

// How many assets to fetch at once
export const BATCH_SIZE = 50;

// Milliseconds we wait until sending a batched query
const BATCHING_INTERVAL = 250;

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

type DataForNodeListener = (stringKey: string, data: LiveDataForNode) => void;

const AssetLiveDataContext = React.createContext<{
  setNeedsImmediateFetch: () => void;
  onSubscribed: () => void;
  onUnsubscribed: () => void;
}>({
  setNeedsImmediateFetch: () => {},
  onSubscribed: () => {},
  onUnsubscribed: () => {},
});

// Map of asset keys to their last fetched time and last requested time
const lastFetchedOrRequested: Record<
  string,
  {fetched: number; requested?: undefined} | {requested: number; fetched?: undefined} | null
> = {};

export const _resetLastFetchedOrRequested = (keys?: AssetKeyInput[]) => {
  (keys?.map((key) => JSON.stringify(key.path)) ?? Object.keys(lastFetchedOrRequested)).forEach(
    (key) => {
      delete lastFetchedOrRequested[key];
    },
  );
};

export const AssetLiveDataProvider = ({children}: {children: React.ReactNode}) => {
  const [needsImmediateFetch, setNeedsImmediateFetch] = React.useState<boolean>(false);
  const [allObservedKeys, setAllObservedKeys] = React.useState<AssetKeyInput[]>([]);
  const [cache, setCache] = React.useState<Record<string, LiveDataForNode>>({});

  const client = useApolloClient();

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

  React.useEffect(() => {
    providerListener = (key, data) => {
      setCache((cache) => {
        return {...cache, [key]: data};
      });
    };
  }, []);

  useDidLaunchEvent(() => {
    _resetLastFetchedOrRequested();
    setNeedsImmediateFetch(true);
  }, SUBSCRIPTION_MAX_POLL_RATE);

  React.useEffect(() => {
    const assetKeyTokens = new Set(allObservedKeys.map(tokenForAssetKey));
    const dataForObservedKeys = allObservedKeys
      .map((key) => cache[tokenForAssetKey(key)])
      .filter((n) => n) as LiveDataForNode[];

    const assetStepKeys = new Set(dataForObservedKeys.flatMap((n) => n.opNames));

    const runInProgressId = uniq(
      dataForObservedKeys.flatMap((p) => [
        ...p.unstartedRunIds,
        ...p.inProgressRunIds,
        ...p.assetChecks
          .map((c) => c.executionForLatestMaterialization)
          .filter(Boolean)
          .map((e) => e!.runId),
      ]),
    ).sort();

    const unobserve = observeAssetEventsInRuns(runInProgressId, (events) => {
      if (
        events.some(
          (e) =>
            (e.assetKey && assetKeyTokens.has(tokenForAssetKey(e.assetKey))) ||
            (e.stepKey && assetStepKeys.has(e.stepKey)),
        )
      ) {
        _resetLastFetchedOrRequested();
      }
    });
    return unobserve;
  }, [allObservedKeys, cache]);

  return (
    <AssetLiveDataContext.Provider
      value={React.useMemo(
        () => ({
          setNeedsImmediateFetch: () => {
            setNeedsImmediateFetch(true);
          },
          onSubscribed: () => {
            setAllObservedKeys(getAllAssetKeysWithListeners());
          },
          onUnsubscribed: () => {
            setAllObservedKeys(getAllAssetKeysWithListeners());
          },
        }),
        [],
      )}
    >
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
  const data = await _queryAssetKeys(client, assetKeys);
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
  assetKey: AssetKeyInput,
  setData: DataForNodeListener,
  setNeedsImmediateFetch: () => void,
) {
  const stringKey = JSON.stringify(assetKey.path);
  _assetKeyListeners[stringKey] = _assetKeyListeners[stringKey] || [];
  _assetKeyListeners[stringKey]!.push(setData);
  const cachedData = _cache[stringKey];
  if (cachedData) {
    setData(stringKey, cachedData);
  } else {
    setNeedsImmediateFetch();
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
      providerListener(key, assetData);
      if (!listeners) {
        return;
      }
      listeners.forEach((listener) => {
        listener(key, assetData);
      });
    });
  });
}

function getAllAssetKeysWithListeners(): AssetKeyInput[] {
  return Object.keys(_assetKeyListeners).map((key) => JSON.parse(key));
}
