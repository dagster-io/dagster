import {ApolloClient} from '@apollo/client';

import {PIPELINE_RUN_LOGS_SUBSCRIPTION} from '../../runs/PipelineRunLogsSubscription';
import {PipelineRunLogsSubscription} from '../../runs/types/PipelineRunLogsSubscription';

export type Message = INITIALIZE;
type INITIALIZE = {
  type: 'INITIALIZE';
  runId: string;
  postMessage: (data: any) => void;
  getApolloClient: () => ApolloClient<any>;
  staticPathRoot: string;
  rootServerURI: string;
};

export function onMainThreadMessage(data: Message) {
  switch (data.type) {
    case 'INITIALIZE':
      initialize(data); // subscribes to the data using data argument
      break;
  }
}

const initialPostMessage = (_data: any): void => {
  throw new Error('Worker not initialized');
};
let postMessage = initialPostMessage;

const start = performance.now();
console.log('start', start);

function initialize(data: INITIALIZE) {
  console.log('initialize');
  postMessage = data.postMessage;
  data
    .getApolloClient()
    .subscribe({
      query: PIPELINE_RUN_LOGS_SUBSCRIPTION,
      fetchPolicy: 'no-cache',
      variables: {runId: data.runId},
    })
    .subscribe({
      next({data}: {data: PipelineRunLogsSubscription}) {
        const logs = data?.pipelineRunLogs;
        if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
          console.error('PipelineRunLogsSubscriptionFailure', logs);
          return;
        }
        console.log('got data', performance.now() - start);
        postMessage(logs);
      },
      error(error: any) {
        console.error(error);
      },
    });
}
