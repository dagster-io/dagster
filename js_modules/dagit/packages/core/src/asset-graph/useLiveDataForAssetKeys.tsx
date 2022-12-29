import {gql, NetworkStatus, useQuery, useSubscription} from '@apollo/client';
import uniq from 'lodash/uniq';
import React from 'react';

import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {graphql} from '../graphql';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {AssetKeyInput} from '../types/globalTypes';

import {buildLiveData, tokenForAssetKey} from './Utils';

const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

/** Fetches the last materialization, "upstream changed", and other live state
 * for the assets in the given pipeline or in the given set of asset keys (or both).
 *
 * Note: The "upstream changed" flag cascades, so it may not appear if the upstream
 * node that has changed is not in scope.
 */
export function useLiveDataForAssetKeys(assetKeys: AssetKeyInput[]) {
  const liveResult = useQuery(ASSETS_GRAPH_LIVE_QUERY, {
    skip: assetKeys.length === 0,
    variables: {assetKeys},
    notifyOnNetworkStatusChange: true,
  });

  const liveDataByNode = React.useMemo(() => {
    return liveResult.data ? buildLiveData(liveResult.data) : {};
  }, [liveResult.data]);

  // Track whether the data is being refetched so incoming asset events don't trigger
  // duplicate requests for live data.
  const fetching = React.useRef(false);
  fetching.current = [NetworkStatus.refetch, NetworkStatus.loading].includes(
    liveResult.networkStatus,
  );

  const timerRef = React.useRef<NodeJS.Timeout | null>(null);

  const onRefreshDebounced = React.useCallback(() => {
    // This is a basic `throttle`, except that if it fires and finds the live
    // query is already refreshing it debounces again.
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
  }, [timerRef, liveResult.refetch]);

  React.useEffect(() => {
    return () => {
      timerRef.current && clearTimeout(timerRef.current);
    };
  }, []);

  // If the event log storage does not support streaming us asset events, fall back to
  // a polling approach and trigger a single refresh when a run is launched for immediate feedback
  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, SUBSCRIPTION_IDLE_POLL_RATE);

  useDidLaunchEvent(liveResult.refetch, SUBSCRIPTION_MAX_POLL_RATE);

  const assetKeyTokens = React.useMemo(() => new Set(assetKeys.map(tokenForAssetKey)), [assetKeys]);
  const assetStepKeys = React.useMemo(
    () => new Set(liveResult.data?.assetNodes.flatMap((n) => n.opNames) || []),
    [liveResult],
  );

  const runInProgressId = uniq(
    Object.values(liveDataByNode).flatMap((p) => [...p.unstartedRunIds, ...p.inProgressRunIds]),
  )
    .sort()
    .slice(0, 3);

  const runWatchers = (
    <>
      {runInProgressId.map((runId) => (
        <RunLogObserver
          runId={runId}
          key={runId}
          assetKeyTokens={assetKeyTokens}
          assetStepKeys={assetStepKeys}
          callback={onRefreshDebounced}
        />
      ))}
    </>
  );

  return {
    liveDataByNode,
    liveDataRefreshState,
    runWatchers,
    assetKeys,
  };
}

const RunLogObserver: React.FC<{
  runId: string;
  assetKeyTokens: Set<string>;
  assetStepKeys: Set<string>;
  callback: () => void;
}> = React.memo(({runId, assetKeyTokens, assetStepKeys, callback}) => {
  // Useful for testing this component:
  const counter = React.useRef(0);
  React.useEffect(() => {
    console.log(`Subscribed to ${runId}`);
    return () => console.log(`Unsubscribed from ${runId} after ${counter.current} messages`);
  }, [runId]);

  useSubscription(ASSET_LIVE_RUN_LOGS_SUBSCRIPTION, {
    fetchPolicy: 'no-cache',
    variables: {runId},
    onSubscriptionData: (data) => {
      const logs = data.subscriptionData.data?.pipelineRunLogs;
      if (logs?.__typename !== 'PipelineRunLogsSubscriptionSuccess') {
        return;
      }

      counter.current += logs.messages.length;

      if (
        logs.messages.some((m) => {
          if (
            m.__typename === 'AssetMaterializationPlannedEvent' ||
            m.__typename === 'MaterializationEvent' ||
            m.__typename === 'ObservationEvent'
          ) {
            return m.assetKey && assetKeyTokens.has(tokenForAssetKey(m.assetKey));
          }
          if (
            m.__typename === 'ExecutionStepFailureEvent' ||
            m.__typename === 'ExecutionStepStartEvent'
          ) {
            return m.stepKey && assetStepKeys.has(m.stepKey);
          }
          return false;
        })
      ) {
        callback();
      }
    },
  });

  return <span />;
});

export const ASSET_LATEST_INFO_FRAGMENT = gql`
  fragment AssetLatestInfoFragment on AssetLatestInfo {
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
    id
  }
`;

const ASSETS_GRAPH_LIVE_QUERY = graphql(`
  query AssetGraphLiveQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys, loadMaterializations: true) {
      id
      ...AssetNodeLiveFragment
    }
    assetsLatestInfo(assetKeys: $assetKeys) {
      ...AssetLatestInfoFragment
    }
  }
`);

const ASSET_LIVE_RUN_LOGS_SUBSCRIPTION = graphql(`
  subscription AssetLiveRunLogsSubscription($runId: ID!) {
    pipelineRunLogs(runId: $runId, cursor: "HEAD") {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          __typename
          ... on AssetMaterializationPlannedEvent {
            assetKey {
              path
            }
          }
          ... on MaterializationEvent {
            assetKey {
              path
            }
          }
          ... on ObservationEvent {
            assetKey {
              path
            }
          }
          ... on ExecutionStepStartEvent {
            stepKey
          }
          ... on ExecutionStepFailureEvent {
            stepKey
          }
        }
      }
    }
  }
`);
