import {gql} from '@apollo/client';

import {RunFragments} from './RunFragments';

export const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $cursor: String) {
    pipelineRunLogs(runId: $runId, cursor: $cursor) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            runId
          }
          ...RunDagsterRunEventFragment
        }
        hasMorePastEvents
        cursor
      }
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
    }
  }
  ${RunFragments.RunDagsterRunEventFragment}
`;
