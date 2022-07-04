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

function initialize(data: INITIALIZE) {
  postMessage = data.postMessage;
  data
    .getApolloClient()
    .subscribe({
      query: PIPELINE_RUN_LOGS_SUBSCRIPTION,
      fetchPolicy: 'no-cache',
      variables: {runId: data.runId},
    })
    .subscribe({
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore - used ApolloClient<any> not sure why this errors
      next(fetchResult: PipelineRunLogsSubscription) {
        const logs = fetchResult?.pipelineRunLogs;
        if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
          return;
        }
        postMessage(logs);
      },
      error(error: any) {
        console.error({error});
      },
    });
}
