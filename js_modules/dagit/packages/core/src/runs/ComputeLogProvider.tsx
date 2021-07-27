import {gql} from '@apollo/client';
import * as React from 'react';

import {DirectGraphQLSubscription} from '../app/DirectGraphQLSubscription';
import {WebSocketContext} from '../app/WebSocketProvider';
import {ComputeIOType} from '../types/globalTypes';

import {COMPUTE_LOG_CONTENT_FRAGMENT, MAX_STREAMING_LOG_BYTES} from './ComputeLogContent';
import {ComputeLogContentFileFragment} from './types/ComputeLogContentFileFragment';
import {ComputeLogsSubscription} from './types/ComputeLogsSubscription';
import {ComputeLogsSubscriptionFragment} from './types/ComputeLogsSubscriptionFragment';

const slice = (s: string) => {
  if (s.length < MAX_STREAMING_LOG_BYTES) {
    return s;
  }
  return s.slice(-MAX_STREAMING_LOG_BYTES);
};

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

interface Props {
  children: (props: {
    isLoading: boolean;
    stdout: ComputeLogsSubscriptionFragment | null;
    stderr: ComputeLogsSubscriptionFragment | null;
  }) => React.ReactChild;
  runId: string;
  stepKey: string;
}

interface State {
  stdout: ComputeLogsSubscriptionFragment | null;
  stderr: ComputeLogsSubscriptionFragment | null;
  isLoading: boolean;
}

type Action =
  | {type: 'initialize'}
  | {type: 'stdout'; messages: ComputeLogsSubscription[]}
  | {type: 'stderr'; messages: ComputeLogsSubscription[]}
  | {type: 'error'};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'initialize':
      return {isLoading: true, stdout: null, stderr: null};
    case 'stdout': {
      let computeLogs: ComputeLogsSubscriptionFragment | null = state.stdout;
      action.messages.forEach((subscription: ComputeLogsSubscription) => {
        computeLogs = merge(computeLogs, subscription.computeLogs);
      });
      return {...state, isLoading: false, stdout: computeLogs};
    }
    case 'stderr': {
      let computeLogs: ComputeLogsSubscriptionFragment | null = state.stderr;
      action.messages.forEach((subscription: ComputeLogsSubscription) => {
        computeLogs = merge(computeLogs, subscription.computeLogs);
      });
      return {...state, isLoading: false, stderr: merge(state.stderr, computeLogs)};
    }
    case 'error':
      return {...state, isLoading: false};
    default:
      return state;
  }
};

const initialState: State = {
  stdout: null,
  stderr: null,
  isLoading: false,
};

export const ComputeLogsProvider = (props: Props) => {
  const {children, runId, stepKey} = props;
  const {connectionParams, websocketURI} = React.useContext(WebSocketContext);
  const [state, dispatch] = React.useReducer(reducer, initialState);

  React.useEffect(() => {
    dispatch({type: 'initialize'});

    const onMessages = (ioType: string, messages: ComputeLogsSubscription[]) => {
      dispatch({type: ioType === 'stdout' ? 'stdout' : 'stderr', messages});
    };

    const onStdout = (messages: ComputeLogsSubscription[]) => onMessages('stdout', messages);
    const onStderr = (messages: ComputeLogsSubscription[]) => onMessages('stderr', messages);
    const onError = () => dispatch({type: 'error'});

    const stdout = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      websocketURI,
      COMPUTE_LOGS_SUBSCRIPTION,
      {runId, stepKey, ioType: ComputeIOType.STDOUT, cursor: null},
      onStdout,
      onError,
      connectionParams,
    );

    const stderr = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      websocketURI,
      COMPUTE_LOGS_SUBSCRIPTION,
      {runId, stepKey, ioType: ComputeIOType.STDERR, cursor: null},
      onStderr,
      onError,
      connectionParams,
    );

    return () => {
      stdout.close();
      stderr.close();
    };
  }, [connectionParams, runId, stepKey, websocketURI]);

  const {isLoading, stdout, stderr} = state;
  return <>{children({isLoading, stdout, stderr})}</>;
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
