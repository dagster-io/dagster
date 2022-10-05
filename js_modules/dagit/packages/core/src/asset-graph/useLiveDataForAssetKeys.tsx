import {
  gql,
  NetworkStatus,
  OnSubscriptionDataOptions,
  useQuery,
  useSubscription,
} from '@apollo/client';
import React from 'react';

import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {AssetKeyInput} from '../types/globalTypes';

import {ASSET_NODE_LIVE_FRAGMENT} from './AssetNode';
import {buildLiveData} from './Utils';
import {AssetGraphLiveQuery, AssetGraphLiveQueryVariables} from './types/AssetGraphLiveQuery';
import {AssetLogEventsSubscription} from './types/AssetLogEventsSubscription';
import {useDidLaunchEvent} from '../runs/RunUtils';

const SUBSCRIPTION_IDLE_POLL_RATE = 120 * 1000;
const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;
const SUBSCRIPTION_UNSUPPORTED_POLL_RATE = 15 * 1000;

/** Fetches the last materialization, "upstream changed", and other live state
 * for the assets in the given pipeline or in the given set of asset keys (or both).
 *
 * Note: The "upstream changed" flag cascades, so it may not appear if the upstream
 * node that has changed is not in scope.
 */
export function useLiveDataForAssetKeys(assetKeys: AssetKeyInput[]) {
  const liveResult = useQuery<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>(
    ASSETS_GRAPH_LIVE_QUERY,
    {
      skip: assetKeys.length === 0,
      variables: {assetKeys},
      notifyOnNetworkStatusChange: true,
    },
  );

  const liveDataByNode = React.useMemo(() => {
    return liveResult.data ? buildLiveData(liveResult.data) : {};
  }, [liveResult.data]);

  // Subscribe to asset events for these asset keys and trigger early refresh of the
  // live query if we think new data will be available.
  const [subscriptionSupported, setSubscriptionSupported] = React.useState(true);

  // Track whether the data is being refetched so incoming asset events don't trigger
  // duplicate requests for live data.
  const fetching = React.useRef(false);
  fetching.current = [NetworkStatus.refetch, NetworkStatus.loading].includes(
    liveResult.networkStatus,
  );

  const timerRef = React.useRef<NodeJS.Timeout | null>(null);
  const onSubscriptionData = React.useCallback(
    (data: OnSubscriptionDataOptions<AssetLogEventsSubscription>) => {
      if (!data.subscriptionData.data) {
        return;
      }
      if (data.subscriptionData.data.__typename !== 'AssetLogEventsSubscriptionSuccess') {
        setSubscriptionSupported(false);
      }

      // This is a basic `throttle`, except that if it fires and finds the live query
      // is already refreshing it debounces again.
      const refetch = liveResult.refetch;
      const fire = () => {
        if (fetching.current) {
          timerRef.current = setTimeout(fire, SUBSCRIPTION_MAX_POLL_RATE);
        } else {
          timerRef.current = null;
          refetch();
        }
      };
      if (!timerRef.current) {
        timerRef.current = setTimeout(fire, SUBSCRIPTION_MAX_POLL_RATE);
      }
      return () => {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
      };
    },
    [timerRef, liveResult.refetch],
  );

  useSubscription<AssetLogEventsSubscription>(ASSET_LOG_EVENTS_SUBSCRIPTION, {
    fetchPolicy: 'no-cache',
    variables: {assetKeys},
    onSubscriptionData: onSubscriptionData,
  });

  // If the event log storage does not support streaming us asset events, fall back to
  // a polling approach and trigger a single refresh when a run is launched for immediate feedback
  const liveDataRefreshState = useQueryRefreshAtInterval(
    liveResult,
    subscriptionSupported ? SUBSCRIPTION_IDLE_POLL_RATE : SUBSCRIPTION_UNSUPPORTED_POLL_RATE,
  );
  useDidLaunchEvent(() => {
    if (!subscriptionSupported) {
      liveResult.refetch();
    }
  });

  return {
    liveResult,
    liveDataByNode,
    liveDataRefreshState,
    assetKeys,
  };
}

export const ASSET_LATEST_INFO_FRAGMENT = gql`
  fragment AssetLatestInfoFragment on AssetLatestInfo {
    assetKey {
      path
    }
    computeStatus
    unstartedRunIds
    inProgressRunIds
    latestRun {
      status
      id
    }
  }
`;

const ASSETS_GRAPH_LIVE_QUERY = gql`
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

const ASSET_LOG_EVENTS_SUBSCRIPTION = gql`
  subscription AssetLogEventsSubscription($assetKeys: [AssetKeyInput!]!) {
    assetLogEvents(assetKeys: $assetKeys) {
      ... on AssetLogEventsSubscriptionSuccess {
        events {
          __typename
        }
      }
      ... on AssetLogEventsSubscriptionFailure {
        message
      }
    }
  }
`;
