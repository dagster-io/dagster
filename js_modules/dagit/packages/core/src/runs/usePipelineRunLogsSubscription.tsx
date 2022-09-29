import React from 'react';

import {AppContext} from '../app/AppContext';
import {arrayBufferToString} from '../workers/util';

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
