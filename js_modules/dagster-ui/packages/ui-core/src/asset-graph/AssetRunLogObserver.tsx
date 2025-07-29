import {memo, useCallback, useEffect, useRef, useState} from 'react';

import {gql, useSubscription} from '../apollo-client';
import {
  AssetLiveRunLogsSubscription,
  AssetLiveRunLogsSubscriptionVariables,
} from './types/AssetRunLogObserver.types';
import {AssetKey} from '../graphql/types';

const OBSERVED_RUNS_CHANGED = 'observed-runs-changed';

type ObservedEvent = {assetKey?: AssetKey; stepKey?: string};
const ObservedRuns: {[runId: string]: ObservedRunCallback[]} = {};

export type ObservedRunCallback = (events: ObservedEvent[]) => void;

function removeCallback(runId: string, callback: ObservedRunCallback) {
  if (!ObservedRuns[runId]) {
    console.log('[ObserveRuns]: Attempted to release runId that has already been released.');
  }
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  ObservedRuns[runId] = ObservedRuns[runId]!.filter((w) => w !== callback);
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  if (ObservedRuns[runId]!.length === 0) {
    delete ObservedRuns[runId];
  }
}

/** Call this function with runIds you'd like to observe and the callback will be invoked when
 * asset events occur in those runs. This function returns an `unsubscribe` method that you
 * should call when your component is unmounted to stop listening.
 */
export function observeAssetEventsInRuns(runIds: string[], callback: ObservedRunCallback) {
  runIds.forEach((runId) => (ObservedRuns[runId] = [...(ObservedRuns[runId] || []), callback]));
  document.dispatchEvent(new CustomEvent(OBSERVED_RUNS_CHANGED));

  return () => {
    // Note: When a component unsubscribes from runs, we immediately remove the callback but we
    // register a temporary one in it's place for one second. This prevents thrashing the subscriptions
    // if you're clicking around the Dagster UI between assets that are all materializing in the same run.
    const temporary: ObservedRunCallback = () => {};
    runIds.forEach((runId) => (ObservedRuns[runId] = [...(ObservedRuns[runId] || []), temporary]));
    runIds.forEach((runId) => removeCallback(runId, callback));
    setTimeout(() => {
      runIds.forEach((runId) => removeCallback(runId, temporary));
      document.dispatchEvent(new CustomEvent(OBSERVED_RUNS_CHANGED));
    }, 1000);
  };
}

export const AssetRunLogObserver = () => {
  const [runIds, setRunIds] = useState<string[]>([]);
  const callback = useCallback((runId: string, events: ObservedEvent[]) => {
    (ObservedRuns[runId] || []).forEach((cb) => cb(events));
  }, []);

  useEffect(() => {
    const listener = () => setRunIds(Object.keys(ObservedRuns));
    document.addEventListener(OBSERVED_RUNS_CHANGED, listener);
    return () => document.removeEventListener(OBSERVED_RUNS_CHANGED, listener);
  }, []);

  return (
    <>
      {runIds.map((runId) => (
        <SingleRunLogObserver runId={runId} key={runId} callback={callback} />
      ))}
    </>
  );
};

interface SingleRunLogObserverProps {
  runId: string;
  callback: (runId: string, events: ObservedEvent[]) => void;
}

const SingleRunLogObserver = memo(({runId, callback}: SingleRunLogObserverProps) => {
  const counter = useRef(0);

  // Useful for testing this component:
  // React.useEffect(() => {
  //   console.log(`Subscribed to ${runId}`);
  //   return () => console.log(`Unsubscribed from ${runId} after ${counter.current} messages`);
  // }, [runId]);

  useSubscription<AssetLiveRunLogsSubscription, AssetLiveRunLogsSubscriptionVariables>(
    ASSET_LIVE_RUN_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables: {runId},
      onSubscriptionData: (data) => {
        const logs = data.subscriptionData.data?.pipelineRunLogs;
        if (logs?.__typename !== 'PipelineRunLogsSubscriptionSuccess') {
          return;
        }

        counter.current += logs.messages.length;

        const relevant = logs.messages
          .map((m) => {
            if (
              m.__typename === 'AssetMaterializationPlannedEvent' ||
              m.__typename === 'MaterializationEvent' ||
              m.__typename === 'ObservationEvent' ||
              m.__typename === 'FailedToMaterializeEvent'
            ) {
              return {assetKey: m.assetKey} as ObservedEvent;
            }
            if (m.__typename === 'AssetCheckEvaluationEvent') {
              return {assetKey: m.evaluation.assetKey} as ObservedEvent;
            }
            if (
              (m.__typename === 'ExecutionStepFailureEvent' ||
                m.__typename === 'ExecutionStepStartEvent') &&
              m.stepKey
            ) {
              return {stepKey: m.stepKey} as ObservedEvent;
            }
            return undefined;
          })
          .filter((a): a is ObservedEvent => !!a);

        if (relevant.length) {
          callback(runId, relevant);
        }
      },
    },
  );

  return <span />;
});

export const ASSET_LIVE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription AssetLiveRunLogsSubscription($runId: ID!) {
    pipelineRunLogs(runId: $runId, cursor: "HEAD") {
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on AssetMaterializationPlannedEvent {
            assetKey {
              path
            }
          }
          ... on AssetCheckEvaluationEvent {
            evaluation {
              assetKey {
                path
              }
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
          ... on FailedToMaterializeEvent {
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
`;
