import {useSubscription} from '@apollo/client';
import React from 'react';

import {AppContext} from '../app/AppContext';
import {arrayBufferToString} from '../workers/util';

import {PIPELINE_RUN_LOGS_SUBSCRIPTION} from './PipelineRunLogsSubscription';
import {
  PipelineRunLogsSubscription,
  PipelineRunLogsSubscriptionVariables,
  PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess,
} from './types/PipelineRunLogsSubscription';

export function usePipelineRunLogsSubscription({runId, cursor}: any, onLogs: any) {
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

export function usePipelineRunLogsSubscriptionWorker(
  {runId}: {runId: string},
  onLogs: (
    result: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess,
  ) => void,
) {
  const {staticPathRoot, rootServerURI} = React.useContext(AppContext);
  React.useEffect(() => {
    const worker = new Worker(new URL('../workers/runLogs/runLogs.worker', import.meta.url));
    worker.postMessage({
      type: 'INITIALIZE',
      runId,
      staticPathRoot,
      rootServerURI,
    });
    let chunks: string[] = [];
    worker.addEventListener('message', (event) => {
      if (event.data === 'startChunk') {
        chunks = [];
      } else if (event.data === 'endChunk') {
        const result = JSON.parse(chunks.join(''));
        chunks = [];
        onLogs(result);
      } else {
        chunks.push(arrayBufferToString(event.data));
      }
    });
    return () => {
      worker.postMessage({
        type: 'SHUTDOWN',
      });
      worker.terminate();
    };
  }, [onLogs, runId, staticPathRoot, rootServerURI]);
}
