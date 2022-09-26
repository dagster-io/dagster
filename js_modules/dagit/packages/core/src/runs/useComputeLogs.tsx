import {gql, useSubscription} from '@apollo/client';
import * as React from 'react';

import {ComputeIOType} from '../types/globalTypes';

import {COMPUTE_LOG_CONTENT_FRAGMENT, MAX_STREAMING_LOG_BYTES} from './ComputeLogContent';
import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';
import {
  ComputeLogsSubscription,
  ComputeLogsSubscriptionVariables,
} from './types/ComputeLogsSubscription';
import {ComputeLogsSubscriptionFragment} from './types/ComputeLogsSubscriptionFragment';

const slice = (s: string) =>
  s.length < MAX_STREAMING_LOG_BYTES ? s : s.slice(-MAX_STREAMING_LOG_BYTES);

const merge = (
  a: ComputeLogContentFileFragment | null,
  b: ComputeLogContentFileFragment | null,
): ComputeLogContentFileFragment | null => {
  if (!b) {
    return a;
  }
  let data = a?.data;
  if (a?.data && b?.data) {
    data = slice(a.data + b.data);
  } else if (b?.data) {
    data = slice(b.data);
  }
  return {
    __typename: b.__typename,
    path: b.path,
    downloadUrl: b.downloadUrl,
    data: typeof data === 'string' ? data : null,
    cursor: b.cursor,
  };
};

interface State {
  stepKey: string;
  stdout: ComputeLogsSubscriptionFragment | null;
  stderr: ComputeLogsSubscriptionFragment | null;
  isLoading: boolean;
}

type Action =
  | {type: 'stdout'; stepKey: string; log: ComputeLogsSubscriptionFragment | null}
  | {type: 'stderr'; stepKey: string; log: ComputeLogsSubscriptionFragment | null};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'stdout':
      const stdout =
        action.stepKey === state.stepKey ? merge(state.stdout, action.log) : action.log;
      return {...state, isLoading: false, stdout};
    case 'stderr':
      const stderr =
        action.stepKey === state.stepKey ? merge(state.stderr, action.log) : action.log;
      return {...state, isLoading: false, stderr};
    default:
      return state;
  }
};

const initialState: State = {
  stepKey: '',
  stdout: null,
  stderr: null,
  isLoading: true,
};

export const useComputeLogs = (runId: string, stepKey: string) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);

  useSubscription<ComputeLogsSubscription, ComputeLogsSubscriptionVariables>(
    COMPUTE_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables: {runId, stepKey, ioType: ComputeIOType.STDOUT, cursor: null},
      onSubscriptionData: ({subscriptionData}) => {
        dispatch({type: 'stdout', stepKey, log: subscriptionData.data?.computeLogs || null});
      },
    },
  );

  useSubscription<ComputeLogsSubscription, ComputeLogsSubscriptionVariables>(
    COMPUTE_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables: {runId, stepKey, ioType: ComputeIOType.STDERR, cursor: null},
      onSubscriptionData: ({subscriptionData}) => {
        dispatch({type: 'stderr', stepKey, log: subscriptionData.data?.computeLogs || null});
      },
    },
  );

  return state;
};

const COMPUTE_LOGS_SUBSCRIPTION_FRAGMENT = gql`
  fragment ComputeLogsSubscriptionFragment on ComputeLogFile {
    data
    cursor
    ...ComputeLogContentFileFragment
  }
  ${COMPUTE_LOG_CONTENT_FRAGMENT}
`;

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $ioType: ComputeIOType!
    $cursor: String
  ) {
    computeLogs(runId: $runId, stepKey: $stepKey, ioType: $ioType, cursor: $cursor) {
      ...ComputeLogsSubscriptionFragment
    }
  }
  ${COMPUTE_LOGS_SUBSCRIPTION_FRAGMENT}
`;
