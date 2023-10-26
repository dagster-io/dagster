import {ApolloClient, gql, useApolloClient} from '@apollo/client';
import uniq from 'lodash/uniq';
import React from 'react';

import {observeAssetEventsInRuns} from '../asset-graph/AssetRunLogObserver';
import {LiveDataForNode, buildLiveDataForNode, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {isDocumentVisible, useDocumentVisibility} from '../hooks/useDocumentVisibility';
import {useDidLaunchEvent} from '../runs/RunUtils';

import {AssetDataRefreshButton} from './AssetDataRefreshButton';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
  AssetNodeLiveFragment,
} from './types/AssetLiveDataProvider.types';

const _assetKeyListeners: Record<string, Array<DataForNodeListener>> = {};
let providerListener = (_key: string, _data?: LiveDataForNode) => {};
const _cache: Record<string, LiveDataForNode> = {};

export function useAssetLiveData(assetKey: AssetKeyInput) {
  const {liveDataByNode, refresh, refreshing} = useAssetsLiveData(
    React.useMemo(() => [assetKey], [assetKey]),
  );
  return {
    liveData: liveDataByNode[tokenForAssetKey(assetKey)],
    refresh,
    refreshing,
  };
}

export function useAssetsLiveData(assetKeys: AssetKeyInput[]) {
  const [data, setData] = React.useState<Record<string, LiveDataForNode>>({});
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const {setNeedsImmediateFetch, onSubscribed, onUnsubscribed} =
    React.useContext(AssetLiveDataContext);

  React.useEffect(() => {
    const setDataSingle = (stringKey: string, assetData?: LiveDataForNode) => {
      setData((data) => {
        const copy = {...data};
        if (!assetData) {
          delete copy[stringKey];
        } else {
          copy[stringKey] = assetData;
        }
        return copy;
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
        const stringKey = tokenForAssetKey(key);
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
    const id = tokenForAssetKey(assetNode.assetKey);
    nodesByKey[id] = assetNode;
  });
  data.assetsLatestInfo.forEach((assetLatestInfo) => {
    const id = tokenForAssetKey(assetLatestInfo.assetKey);
    liveDataByKey[id] = buildLiveDataForNode(nodesByKey[id]!, assetLatestInfo);
  });
  Object.assign(_cache, liveDataByKey);
  return liveDataByKey;
}

// How many assets to fetch at once
export const BATCH_SIZE = 10;

// Milliseconds we wait until sending a batched query
const BATCHING_INTERVAL = 250;

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

export const LiveDataPollRateContext = React.createContext<number>(SUBSCRIPTION_IDLE_POLL_RATE);

type DataForNodeListener = (stringKey: string, data?: LiveDataForNode) => void;

const AssetLiveDataContext = React.createContext<{
  setNeedsImmediateFetch: () => void;
  onSubscribed: () => void;
  onUnsubscribed: () => void;
}>({
  setNeedsImmediateFetch: () => {},
  onSubscribed: () => {},
  onUnsubscribed: () => {},
});

const AssetLiveDataRefreshContext = React.createContext<{
  isGloballyRefreshing: boolean;
  oldestDataTimestamp: number;
  refresh: () => void;
}>({
  isGloballyRefreshing: false,
  oldestDataTimestamp: Infinity,
  refresh: () => {},
});

// Map of asset keys to their last fetched time and last requested time
const lastFetchedOrRequested: Record<
  string,
  {fetched: number; requested?: undefined} | {requested: number; fetched?: undefined} | null
> = {};

export const _resetLastFetchedOrRequested = (keys?: AssetKeyInput[]) => {
  (keys?.map((key) => tokenForAssetKey(key)) ?? Object.keys(lastFetchedOrRequested)).forEach(
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

  const [isGloballyRefreshing, setIsGloballyRefreshing] = React.useState(false);
  const [oldestDataTimestamp, setOldestDataTimestamp] = React.useState(0);

  const onUpdatingOrUpdated = React.useCallback(() => {
    const allAssetKeys = Object.keys(_assetKeyListeners).filter(
      (key) => _assetKeyListeners[key]?.length,
    );
    let isRefreshing = allAssetKeys.length ? true : false;
    let oldestDataTimestamp = Infinity;
    for (const key of allAssetKeys) {
      if (lastFetchedOrRequested[key]?.fetched) {
        isRefreshing = false;
      }
      oldestDataTimestamp = Math.min(
        oldestDataTimestamp,
        lastFetchedOrRequested[key]?.fetched ?? Infinity,
      );
    }
    setIsGloballyRefreshing(isRefreshing);
    setOldestDataTimestamp(oldestDataTimestamp === Infinity ? 0 : oldestDataTimestamp);
  }, []);

  const pollRate = React.useContext(LiveDataPollRateContext);

  React.useEffect(() => {
    if (!isDocumentVisible) {
      return;
    }
    // Check for assets to fetch every 5 seconds to simplify logic
    // This means assets will be fetched at most 5 + SUBSCRIPTION_IDLE_POLL_RATE after their first fetch
    // but then will be fetched every SUBSCRIPTION_IDLE_POLL_RATE after that
    const interval = setInterval(
      () => fetchData(client, pollRate, onUpdatingOrUpdated),
      Math.min(pollRate, 5000),
    );
    fetchData(client, pollRate, onUpdatingOrUpdated);
    return () => {
      clearInterval(interval);
    };
  }, [client, pollRate, isDocumentVisible, onUpdatingOrUpdated]);

  React.useEffect(() => {
    if (!needsImmediateFetch) {
      return;
    }
    const timeout = setTimeout(() => {
      fetchData(client, pollRate, onUpdatingOrUpdated);
      setNeedsImmediateFetch(false);
      // Wait BATCHING_INTERVAL before doing fetch in case the component is unmounted quickly (eg. in the case of scrolling/filtering quickly)
    }, BATCHING_INTERVAL);
    return () => {
      clearTimeout(timeout);
    };
  }, [client, needsImmediateFetch, pollRate, onUpdatingOrUpdated]);

  React.useEffect(() => {
    providerListener = (stringKey, assetData) => {
      setCache((data) => {
        const copy = {...data};
        if (!assetData) {
          delete copy[stringKey];
        } else {
          copy[stringKey] = assetData;
        }
        return copy;
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
      <AssetLiveDataRefreshContext.Provider
        value={{
          isGloballyRefreshing,
          oldestDataTimestamp,
          refresh: React.useCallback(() => {
            setIsGloballyRefreshing(true);
            _resetLastFetchedOrRequested();
            setNeedsImmediateFetch(true);
          }, [setNeedsImmediateFetch]),
        }}
      >
        {children}
      </AssetLiveDataRefreshContext.Provider>
    </AssetLiveDataContext.Provider>
  );
};

let isFetching = false;
async function _batchedQueryAssets(
  assetKeys: AssetKeyInput[],
  client: ApolloClient<any>,
  pollRate: number,
  setData: (data: Record<string, LiveDataForNode>) => void,
  onUpdatingOrUpdated: () => void,
) {
  // Bail if the document isn't visible
  if (!assetKeys.length || isFetching) {
    return;
  }
  isFetching = true;
  // Use Date.now because it properly advances in jest with fakeTimers /shrug
  const requestTime = Date.now();
  assetKeys.forEach((key) => {
    lastFetchedOrRequested[tokenForAssetKey(key)] = {
      requested: requestTime,
    };
  });
  onUpdatingOrUpdated();

  function doNextFetch(pollRate: number) {
    isFetching = false;
    const nextAssets = _determineAssetsToFetch(pollRate);
    if (nextAssets.length) {
      _batchedQueryAssets(nextAssets, client, pollRate, setData, onUpdatingOrUpdated);
    }
  }
  try {
    const data = await _queryAssetKeys(client, assetKeys);
    const fetchedTime = Date.now();
    assetKeys.forEach((key) => {
      lastFetchedOrRequested[tokenForAssetKey(key)] = {
        fetched: fetchedTime,
      };
    });
    setData(data);
    onUpdatingOrUpdated();
    doNextFetch(pollRate);
  } catch (e) {
    console.error(e);

    if ((e as any)?.message?.includes('500')) {
      // Mark these assets as fetched so that we don't retry them until after the poll interval rather than retrying them immediately.
      // This is preferable because if the assets failed to fetch it's likely due to a timeout due to the query being too expensive and retrying it
      // will not make it more likely to succeed and it would add more load to the database.
      const fetchedTime = Date.now();
      assetKeys.forEach((key) => {
        lastFetchedOrRequested[tokenForAssetKey(key)] = {
          fetched: fetchedTime,
        };
      });
    } else {
      // If it's not a timeout from the backend then lets keep retrying instead of moving on.
      assetKeys.forEach((key) => {
        delete lastFetchedOrRequested[tokenForAssetKey(key)];
      });
    }

    setTimeout(doNextFetch, Math.min(pollRate, 5000));
  }
}

function _subscribeToAssetKey(
  assetKey: AssetKeyInput,
  setData: DataForNodeListener,
  setNeedsImmediateFetch: () => void,
) {
  const stringKey = tokenForAssetKey(assetKey);
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
  const stringKey = tokenForAssetKey(assetKey);
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
function _determineAssetsToFetch(pollRate: number) {
  const assetsToFetch: AssetKeyInput[] = [];
  const assetsWithoutData: AssetKeyInput[] = [];
  const allKeys = Object.keys(_assetKeyListeners);
  while (allKeys.length && assetsWithoutData.length < BATCH_SIZE) {
    const key = allKeys.shift()!;
    const isRequested = !!lastFetchedOrRequested[key]?.requested;
    if (isRequested) {
      continue;
    }
    const lastFetchTime = lastFetchedOrRequested[key]?.fetched ?? null;
    if (lastFetchTime !== null && Date.now() - lastFetchTime < pollRate) {
      continue;
    }
    if (lastFetchTime && isDocumentVisible()) {
      assetsToFetch.push({path: key.split('/')});
    } else {
      assetsWithoutData.push({path: key.split('/')});
    }
  }

  // Prioritize fetching assets for which there is no data in the cache
  return assetsWithoutData.concat(assetsToFetch).slice(0, BATCH_SIZE);
}

function fetchData(client: ApolloClient<any>, pollRate: number, onUpdatingOrUpdated: () => void) {
  _batchedQueryAssets(
    _determineAssetsToFetch(pollRate),
    client,
    pollRate,
    (data) => {
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
    },
    onUpdatingOrUpdated,
  );
}

function getAllAssetKeysWithListeners(): AssetKeyInput[] {
  return Object.keys(_assetKeyListeners).map((key) => ({path: key.split('/')}));
}

export function _setCacheEntryForTest(assetKey: AssetKeyInput, data?: LiveDataForNode) {
  if (process.env.STORYBOOK || typeof jest !== 'undefined') {
    const stringKey = tokenForAssetKey(assetKey);
    if (data) {
      _cache[stringKey] = data;
    } else {
      delete _cache[stringKey];
    }
    const listeners = _assetKeyListeners[stringKey];
    providerListener(stringKey, data);
    if (!listeners) {
      return;
    }
    listeners.forEach((listener) => {
      listener(stringKey, data);
    });
  }
}

export function AssetLiveDataRefresh() {
  const {isGloballyRefreshing, oldestDataTimestamp, refresh} = React.useContext(
    AssetLiveDataRefreshContext,
  );
  return (
    <AssetDataRefreshButton
      isRefreshing={isGloballyRefreshing}
      oldestDataTimestamp={oldestDataTimestamp}
      onRefresh={refresh}
    />
  );
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
    assetChecks {
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
    freshnessInfo {
      ...AssetNodeLiveFreshnessInfo
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
`;

export const ASSETS_GRAPH_LIVE_QUERY = gql`
  query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
    assetsLatestInfo(assetKeys: $assetKeys) {
      ...AssetLatestInfoFragment
    }
  }

  ${ASSET_NODE_LIVE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;
