import {useSubscription} from '@apollo/client';
import React from 'react';

import {AppContext} from '../app/AppContext';
import {arrayBufferToString} from '../workers/util';

import {PIPELINE_RUN_LOGS_SUBSCRIPTION} from './PipelineRunLogsSubscription';
import {
  PipelineRunLogsSubscription,
  PipelineRunLogsSubscriptionVariables,
} from './types/PipelineRunLogsSubscription';

export function usePipelineRunLogsSubscription({runId, cursor}: any, onLogs: any) {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useSubscription<PipelineRunLogsSubscription, PipelineRunLogsSubscriptionVariables>(
    PIPELINE_RUN_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables: {runId, cursor},
      onSubscriptionData: ({subscriptionData}) => {
        const logs = subscriptionData.data?.pipelineRunLogs;
        if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
          return;
        }
        onLogs(logs);
      },
    },
  );
}

export function usePipelineRunLogsSubscriptionWorker({runId}: any, onLogs: any) {
  const {staticPathRoot, rootServerURI} = React.useContext(AppContext);
  React.useEffect(() => {
    const worker = new Worker(new URL('../workers/runLogs/runLogs.worker', import.meta.url));
    worker.postMessage({
      type: 'INITIALIZE',
      runId,
      staticPathRoot,
      rootServerURI,
    });
    worker.addEventListener('message', (event) => {
      try {
        onLogs(JSON.parse(arrayBufferToString(event.data)));
      } catch (_) {}
    });
    return () => {
      worker.postMessage({
        type: 'SHUTDOWN',
      });
      worker.terminate();
    };
  }, [onLogs, runId, staticPathRoot, rootServerURI]);
}
