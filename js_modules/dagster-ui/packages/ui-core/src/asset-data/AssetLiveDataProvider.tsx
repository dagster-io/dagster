import {ApolloClient, gql, useApolloClient} from '@apollo/client';
import uniq from 'lodash/uniq';
import React from 'react';

import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from './types/AssetLiveDataProvider.types';
import {SUBSCRIPTION_MAX_POLL_RATE} from './util';
import {observeAssetEventsInRuns} from '../asset-graph/AssetRunLogObserver';
import {
  LiveDataForNode,
  buildLiveDataForNode,
  tokenForAssetKey,
  tokenToAssetKey,
} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataPollRateContext} from '../live-data-provider/LiveDataProvider';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useDidLaunchEvent} from '../runs/RunUtils';

function makeFactory() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      const {data} = await client.query<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
        query: ASSETS_GRAPH_LIVE_QUERY,
        fetchPolicy: 'network-only',
        variables: {
          assetKeys: keys.map(tokenToAssetKey),
        },
      });
      const nodesByKey = Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );

      const liveDataByKey = Object.fromEntries(
        data.assetsLatestInfo.map((assetLatestInfo) => {
          const id = tokenForAssetKey(assetLatestInfo.assetKey);
          return [id, buildLiveDataForNode(nodesByKey[id]!, assetLatestInfo)];
        }),
      );
      return liveDataByKey;
    },
  );
}
export const factory = makeFactory();

export function useAssetLiveData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  return factory.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
}

export function useAssetsLiveData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'default',
) {
  return factory.useLiveData(
    assetKeys.map((key) => tokenForAssetKey(key)),
    thread,
  );
}

export const AssetLiveDataProvider = ({children}: {children: React.ReactNode}) => {
  const [allObservedKeys, setAllObservedKeys] = React.useState<AssetKeyInput[]>([]);

  React.useEffect(() => {
    factory.manager.setOnSubscriptionsChangedCallback((keys) =>
      setAllObservedKeys(keys.map((key) => ({path: key.split('/')}))),
    );
  }, []);

  const pollRate = React.useContext(LiveDataPollRateContext);

  React.useEffect(() => {
    factory.manager.setPollRate(pollRate);
  }, [pollRate]);

  useDidLaunchEvent(() => {
    factory.manager.refreshKeys();
  }, SUBSCRIPTION_MAX_POLL_RATE);

  React.useEffect(() => {
    const assetKeyTokens = new Set(allObservedKeys.map(tokenForAssetKey));
    const dataForObservedKeys = allObservedKeys
      .map((key) => factory.manager.getCacheEntry(tokenForAssetKey(key)))
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
        factory.manager.refreshKeys();
      }
    });
    return unobserve;
  }, [allObservedKeys]);

  return <factory.LiveDataProvider>{children}</factory.LiveDataProvider>;
};

export function AssetLiveDataRefreshButton() {
  return <factory.LiveDataRefresh />;
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
  Object.assign(factory, makeFactory());
}
