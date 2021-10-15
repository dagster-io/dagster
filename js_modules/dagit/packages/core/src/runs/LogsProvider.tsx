import {gql, useApolloClient, useQuery, useSubscription} from '@apollo/client';
import throttle from 'lodash/throttle';
import * as React from 'react';

import {WebSocketContext} from '../app/WebSocketProvider';
import {PipelineRunStatus} from '../types/globalTypes';
import {TokenizingFieldValue} from '../ui/TokenizingField';

import {RunFragments} from './RunFragments';
import {PipelineRunLogsSubscription} from './types/PipelineRunLogsSubscription';
import {PipelineRunLogsSubscriptionStatusFragment} from './types/PipelineRunLogsSubscriptionStatusFragment';
import {RunDagsterRunEventFragment} from './types/RunDagsterRunEventFragment';
import {RunLogsQuery} from './types/RunLogsQuery';

export interface LogFilterValue extends TokenizingFieldValue {
  token?: 'step' | 'type' | 'query';
}

export interface LogFilter {
  logQuery: LogFilterValue[];
  levels: {[key: string]: boolean};
  focusedTime: number;
  sinceTime: number;
  hideNonMatches: boolean;
}

type LogNode = RunDagsterRunEventFragment & {clientsideKey: string};
type Nodes = LogNode[];

export interface LogsProviderLogs {
  allNodes: LogNode[];
  loading: boolean;
}

const pipelineStatusFromMessages = (messages: RunDagsterRunEventFragment[]) => {
  const reversed = [...messages].reverse();
  for (const message of reversed) {
    const {__typename} = message;
    switch (__typename) {
      case 'RunStartEvent':
        return PipelineRunStatus.STARTED;
      case 'RunEnqueuedEvent':
        return PipelineRunStatus.QUEUED;
      case 'RunStartingEvent':
        return PipelineRunStatus.STARTING;
      case 'RunCancelingEvent':
        return PipelineRunStatus.CANCELING;
      case 'RunCanceledEvent':
        return PipelineRunStatus.CANCELED;
      case 'RunSuccessEvent':
        return PipelineRunStatus.SUCCESS;
      case 'RunFailureEvent':
        return PipelineRunStatus.FAILURE;
    }
  }
  return null;
};

const BATCH_INTERVAL = 100;

type State = {
  nodes: Nodes;
  cursor: number;
  loading: boolean;
};

type Action =
  | {type: 'append'; queued: RunDagsterRunEventFragment[]; hasMore: boolean}
  | {type: 'set-cursor'}
  | {type: 'reset'};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'append':
      const nodes = [...state.nodes, ...action.queued].map((m, idx) => ({
        ...m,
        clientsideKey: `csk${idx}`,
      }));
      return {...state, nodes, loading: action.hasMore};
    case 'set-cursor':
      return {...state, cursor: state.nodes.length - 1};
    case 'reset':
      return {nodes: [], cursor: -1, loading: true};
    default:
      return state;
  }
};

const initialState = {
  nodes: [],
  cursor: -1,
  loading: true,
};

const useLogsProviderWithSubscription = (runId: string) => {
  const client = useApolloClient();
  const {websocketClient} = React.useContext(WebSocketContext);
  const queue = React.useRef<RunDagsterRunEventFragment[]>([]);
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const syncPipelineStatusToApolloCache = React.useCallback(
    (status: PipelineRunStatus) => {
      const local = client.readFragment<PipelineRunLogsSubscriptionStatusFragment>({
        fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
        fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
        id: `PipelineRun:${runId}`,
      });

      if (local) {
        const toWrite = {...local, status};
        if (
          status === PipelineRunStatus.FAILURE ||
          status === PipelineRunStatus.SUCCESS ||
          status === PipelineRunStatus.STARTING ||
          status === PipelineRunStatus.CANCELING ||
          status === PipelineRunStatus.CANCELED
        ) {
          toWrite.canTerminate = false;
        }
        client.writeFragment({
          fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
          fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
          id: `PipelineRun:${runId}`,
          data: toWrite,
        });
      }
    },
    [client, runId],
  );

  // If the WebSocket disconnects, move the cursor to the end to ensure that we don't
  // incorrectly refetch logs that we already have.
  React.useEffect(() => {
    const unlisten = websocketClient?.onDisconnected(() => dispatch({type: 'set-cursor'}));
    return () => unlisten && unlisten();
  }, [websocketClient]);

  React.useEffect(() => {
    queue.current = [];
    dispatch({type: 'reset'});
  }, [runId]);

  // Batch the nodes together so they don't overwhelm the animation of the Gantt,
  // which depends on a bit of a timing delay to maintain smoothness.
  const throttledSetNodes = React.useMemo(() => {
    return throttle((hasMore: boolean) => {
      const queued = [...queue.current];
      queue.current = [];
      dispatch({type: 'append', queued, hasMore});
    }, BATCH_INTERVAL);
  }, []);

  const {nodes, cursor, loading} = state;

  useSubscription<PipelineRunLogsSubscription>(PIPELINE_RUN_LOGS_SUBSCRIPTION, {
    fetchPolicy: 'no-cache',
    variables: {runId, after: cursor},
    onSubscriptionData: ({subscriptionData}) => {
      const logs = subscriptionData.data?.pipelineRunLogs;
      if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
        return;
      }

      const {messages, hasMorePastEvents} = logs;
      const nextPipelineStatus = pipelineStatusFromMessages(messages);

      // If we're still loading past events, don't sync to the cache -- event chunks could
      // give us `status` values that don't match the actual state of the run.
      if (nextPipelineStatus && !hasMorePastEvents) {
        syncPipelineStatusToApolloCache(nextPipelineStatus);
      }

      // Maintain a queue of messages as they arrive, and call the throttled setter.
      queue.current = [...queue.current, ...messages];
      throttledSetNodes(hasMorePastEvents);
    },
  });

  return React.useMemo(
    () => (nodes !== null ? {allNodes: nodes, loading} : {allNodes: [], loading}),
    [loading, nodes],
  );
};

interface LogsProviderProps {
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

const LogsProviderWithSubscription: React.FC<LogsProviderProps> = (props) => {
  const state = useLogsProviderWithSubscription(props.runId);
  return <>{props.children(state)}</>;
};

interface LogsProviderWithQueryProps {
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

const POLL_INTERVAL = 5000;

const LogsProviderWithQuery = (props: LogsProviderWithQueryProps) => {
  const {children, runId} = props;
  const [nodes, setNodes] = React.useState<LogNode[]>(() => []);
  const [after, setAfter] = React.useState<number>(-1);

  const {stopPolling, startPolling} = useQuery<RunLogsQuery>(RUN_LOGS_QUERY, {
    notifyOnNetworkStatusChange: true,
    variables: {runId, after},
    pollInterval: POLL_INTERVAL,
    onCompleted: (data: RunLogsQuery) => {
      // We have to stop polling in order to update the `after` value.
      stopPolling();

      const slice = () => {
        const count = nodes.length;
        if (data?.pipelineRunOrError.__typename === 'PipelineRun') {
          return data?.pipelineRunOrError.events.map((event, ii) => ({
            ...event,
            clientsideKey: `csk${count + ii}`,
          }));
        }
        return [];
      };

      const newSlice = slice();
      setNodes((current) => [...current, ...newSlice]);
      setAfter((current) => current + newSlice.length);

      const status =
        data?.pipelineRunOrError.__typename === 'PipelineRun'
          ? data?.pipelineRunOrError.status
          : null;

      if (
        status &&
        status !== PipelineRunStatus.FAILURE &&
        status !== PipelineRunStatus.SUCCESS &&
        status !== PipelineRunStatus.CANCELED
      ) {
        startPolling(POLL_INTERVAL);
      }
    },
  });

  return (
    <>
      {children(
        nodes !== null && nodes.length > 0
          ? {allNodes: nodes, loading: false}
          : {allNodes: [], loading: true},
      )}
    </>
  );
};

export const LogsProvider: React.FC<LogsProviderProps> = (props) => {
  const {children, runId} = props;
  const {availability} = React.useContext(WebSocketContext);

  if (availability === 'attempting-to-connect') {
    return <>{children({allNodes: [], loading: true})}</>;
  }

  if (availability === 'unavailable') {
    return <LogsProviderWithQuery runId={runId}>{children}</LogsProviderWithQuery>;
  }

  return <LogsProviderWithSubscription runId={runId}>{children}</LogsProviderWithSubscription>;
};

const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $after: Cursor) {
    pipelineRunLogs(runId: $runId, after: $after) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            runId
          }
          ...RunDagsterRunEventFragment
        }
        hasMorePastEvents
      }
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
    }
  }

  ${RunFragments.RunDagsterRunEventFragment}
`;

const PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT = gql`
  fragment PipelineRunLogsSubscriptionStatusFragment on PipelineRun {
    id
    runId
    status
    canTerminate
  }
`;

const RUN_LOGS_QUERY = gql`
  query RunLogsQuery($runId: ID!, $after: Cursor) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        id
        runId
        status
        canTerminate
        events(after: $after) {
          ... on MessageEvent {
            runId
          }
          ...RunDagsterRunEventFragment
          __typename
        }
      }
    }
  }
  ${RunFragments.RunDagsterRunEventFragment}
`;
