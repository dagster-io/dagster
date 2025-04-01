import {TokenizingFieldValue} from '@dagster-io/ui-components';
import throttle from 'lodash/throttle';
import * as React from 'react';

import {LogLevelCounts} from './LogsToolbar';
import {RUN_DAGSTER_RUN_EVENT_FRAGMENT} from './RunFragments';
import {logNodeLevel} from './logNodeLevel';
import {LogNode} from './types';
import {
  OnSubscriptionDataOptions,
  gql,
  useApolloClient,
  useQuery,
  useSubscription,
} from '../apollo-client';
import {
  PipelineRunLogsSubscription,
  PipelineRunLogsSubscriptionStatusFragment,
  PipelineRunLogsSubscriptionVariables,
  RunLogsQuery,
  RunLogsQueryVariables,
  RunLogsSubscriptionSuccessFragment,
} from './types/LogsProvider.types';
import {RunDagsterRunEventFragment} from './types/RunFragments.types';
import {WebSocketContext} from '../app/WebSocketProvider';
import {RunStatus} from '../graphql/types';
import {CompletionType, useTraceDependency} from '../performance/TraceContext';

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

export interface LogsProviderLogs {
  allNodeChunks: LogNode[][];
  counts: LogLevelCounts;
  loading: boolean;
}

const pipelineStatusFromMessages = (messages: RunDagsterRunEventFragment[]) => {
  const reversed = [...messages].reverse();
  for (const message of reversed) {
    const {__typename} = message;
    switch (__typename) {
      case 'RunStartEvent':
        return RunStatus.STARTED;
      case 'RunEnqueuedEvent':
        return RunStatus.QUEUED;
      case 'RunStartingEvent':
        return RunStatus.STARTING;
      case 'RunCancelingEvent':
        return RunStatus.CANCELING;
      case 'RunCanceledEvent':
        return RunStatus.CANCELED;
      case 'RunSuccessEvent':
        return RunStatus.SUCCESS;
      case 'RunFailureEvent':
        return RunStatus.FAILURE;
    }
  }
  return null;
};

const BATCH_INTERVAL = 100;
const QUERY_LOG_LIMIT = 1000;

type State = {
  nodeChunks: LogNode[][];
  cursor: string | null;
  counts: LogLevelCounts;
  loading: boolean;
};

type Action =
  | {type: 'append'; queued: RunDagsterRunEventFragment[]; hasMore: boolean; cursor: string}
  | {type: 'set-cursor'; cursor: string}
  | {type: 'reset'};

const emptyCounts = {
  DEBUG: 0,
  INFO: 0,
  WARNING: 0,
  ERROR: 0,
  CRITICAL: 0,
  EVENT: 0,
};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'append': {
      const queuedNodes = action.queued.map((node, ii) => ({
        ...node,
        clientsideKey: `csk${node.timestamp}-${ii}`,
      }));

      const copy = state.nodeChunks.slice();
      copy.push(queuedNodes);

      const counts = {...state.counts};
      queuedNodes.forEach((node) => {
        const level = logNodeLevel(node);
        counts[level]++;
      });

      return {nodeChunks: copy, counts, loading: action.hasMore, cursor: action.cursor};
    }
    case 'set-cursor':
      return {...state, cursor: action.cursor};
    case 'reset':
      return {nodeChunks: [], counts: emptyCounts, cursor: null, loading: true};
    default:
      return state;
  }
};

const initialState: State = {
  nodeChunks: [] as LogNode[][],
  counts: emptyCounts,
  cursor: null,
  loading: true,
};

const useLogsProviderWithSubscription = (runId: string) => {
  const client = useApolloClient();
  const queue = React.useRef<RunLogsSubscriptionSuccessFragment[]>([]);
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const syncPipelineStatusToApolloCache = React.useCallback(
    (status: RunStatus) => {
      const local = client.readFragment<PipelineRunLogsSubscriptionStatusFragment>({
        fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
        fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
        id: `Run:${runId}`,
      });

      if (local) {
        const toWrite = {
          ...local,
          canTerminate: status === RunStatus.QUEUED || status === RunStatus.STARTED,
          status,
        };

        client.writeFragment({
          fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
          fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
          id: `Run:${runId}`,
          data: toWrite,
        });
      }
    },
    [client, runId],
  );

  React.useEffect(() => {
    queue.current = [];
    dispatch({type: 'reset'});
  }, [runId]);

  // Batch the nodes together so they don't overwhelm the animation of the Gantt,
  // which depends on a bit of a timing delay to maintain smoothness.
  const throttledSetNodes = React.useMemo(() => {
    return throttle(() => {
      if (!queue.current.length) {
        return;
      }
      const queuedLogs = [...queue.current];
      queue.current = [];
      const queuedMessages = queuedLogs.flatMap((log) => log.messages);
      const lastLog = queuedLogs[queuedLogs.length - 1]!;
      const hasMore = lastLog.hasMorePastEvents;
      const cursor = lastLog.cursor;

      dispatch({type: 'append', queued: queuedMessages, hasMore, cursor});
      const nextPipelineStatus = pipelineStatusFromMessages(queuedMessages);

      // If we're still loading past events, don't sync to the cache -- event chunks could
      // give us `status` values that don't match the actual state of the run.
      if (nextPipelineStatus && !hasMore) {
        syncPipelineStatusToApolloCache(nextPipelineStatus);
      }
    }, BATCH_INTERVAL);
  }, [syncPipelineStatusToApolloCache]);

  const {nodeChunks, counts, cursor, loading} = state;

  const {availability, disabled, status} = React.useContext(WebSocketContext);
  const lostWebsocket = !disabled && availability === 'available' && status === WebSocket.CLOSED;
  const currentInitialCursorRef = React.useRef<string | null>(cursor);

  if (lostWebsocket) {
    // Record the cursor we're at when disconnecting so that our subscription
    // picks up where we left off.
    currentInitialCursorRef.current = cursor;
  }
  const currentInitialCursor = currentInitialCursorRef.current;

  const variables = React.useMemo(() => {
    return {
      runId,
      cursor: currentInitialCursor,
    };
  }, [runId, currentInitialCursor]);

  const subscriptionComponent = React.useMemo(
    () => (
      <SubscriptionComponent
        variables={variables}
        onSubscriptionData={({subscriptionData}) => {
          const logs = subscriptionData.data?.pipelineRunLogs;
          if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
            return;
          }
          // Maintain a queue of messages as they arrive, and call the throttled setter.
          queue.current.push(logs);
          // Wait until end of animation frame to call throttled set nodes
          // otherwise we wont end up batching anything if rendering takes
          // longer than the BATCH_INTERVAL
          requestAnimationFrame(throttledSetNodes);
        }}
      />
    ),
    [variables, throttledSetNodes],
  );

  return React.useMemo(
    () =>
      nodeChunks !== null
        ? {allNodeChunks: nodeChunks, counts, loading, subscriptionComponent}
        : {allNodeChunks: [], counts, loading, subscriptionComponent},
    [counts, loading, nodeChunks, subscriptionComponent],
  );
};

/**
 * Putting useSubscription in a component that returns null avoids re-rendering
 * any children components that aren't completely memoized
 * https://stackoverflow.com/questions/61876931/how-to-prevent-re-rendering-with-usesubscription
 */
const SubscriptionComponent = ({
  variables,
  onSubscriptionData,
}: {
  variables: {
    runId: string;
    cursor: string | null;
  };
  onSubscriptionData: (options: OnSubscriptionDataOptions<PipelineRunLogsSubscription>) => void;
}) => {
  useSubscription<PipelineRunLogsSubscription, PipelineRunLogsSubscriptionVariables>(
    PIPELINE_RUN_LOGS_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      variables,
      onSubscriptionData,
    },
  );
  return null;
};

interface LogsProviderProps {
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

const LogsProviderWithSubscription = (props: LogsProviderProps) => {
  const state = useLogsProviderWithSubscription(props.runId);
  return (
    <>
      {state.subscriptionComponent}
      {props.children(state)}
    </>
  );
};

interface LogsProviderWithQueryProps {
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

const POLL_INTERVAL = 5000;

const LogsProviderWithQuery = (props: LogsProviderWithQueryProps) => {
  const {children, runId} = props;
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {counts, cursor, nodeChunks} = state;

  const dependency = useTraceDependency('RunLogsQuery');

  const {stopPolling, startPolling} = useQuery<RunLogsQuery, RunLogsQueryVariables>(
    RUN_LOGS_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      fetchPolicy: 'no-cache',
      variables: {runId, cursor, limit: QUERY_LOG_LIMIT},
      pollInterval: POLL_INTERVAL,
      onCompleted: (data: RunLogsQuery) => {
        // We have to stop polling in order to update the `after` value.
        stopPolling();

        if (
          data?.pipelineRunOrError.__typename !== 'Run' ||
          data?.logsForRun.__typename !== 'EventConnection'
        ) {
          dependency.completeDependency(CompletionType.ERROR);
          return;
        }

        const run = data.pipelineRunOrError;
        const queued = data.logsForRun.events;
        const status = run.status;
        const cursor = data.logsForRun.cursor;

        const hasMore =
          !!status &&
          status !== RunStatus.FAILURE &&
          status !== RunStatus.SUCCESS &&
          status !== RunStatus.CANCELED;

        dispatch({type: 'append', queued, hasMore, cursor});
        dependency.completeDependency(CompletionType.SUCCESS);

        if (hasMore) {
          startPolling(POLL_INTERVAL);
        }
      },
    },
  );

  return (
    <>
      {children(
        nodeChunks !== null && nodeChunks.length > 0
          ? {allNodeChunks: nodeChunks, counts, loading: false}
          : {allNodeChunks: [], counts, loading: true},
      )}
    </>
  );
};

export const LogsProvider = (props: LogsProviderProps) => {
  const {children, runId} = props;
  const {availability, disabled} = React.useContext(WebSocketContext);

  // if disabled, drop to query variant immediately
  if (availability === 'unavailable' || disabled) {
    return <LogsProviderWithQuery runId={runId}>{children}</LogsProviderWithQuery>;
  }

  if (availability === 'attempting-to-connect') {
    return <>{children({allNodeChunks: [], counts: emptyCounts, loading: true})}</>;
  }

  return <LogsProviderWithSubscription runId={runId}>{children}</LogsProviderWithSubscription>;
};

const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $cursor: String) {
    pipelineRunLogs(runId: $runId, cursor: $cursor) {
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
      ...RunLogsSubscriptionSuccess
    }
  }

  fragment RunLogsSubscriptionSuccess on PipelineRunLogsSubscriptionSuccess {
    messages {
      ... on MessageEvent {
        runId
      }
      ...RunDagsterRunEventFragment
    }
    hasMorePastEvents
    cursor
  }

  ${RUN_DAGSTER_RUN_EVENT_FRAGMENT}
`;

const PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT = gql`
  fragment PipelineRunLogsSubscriptionStatusFragment on Run {
    id
    status
    canTerminate
  }
`;

const RUN_LOGS_QUERY = gql`
  query RunLogsQuery($runId: ID!, $cursor: String, $limit: Int) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        status
        canTerminate
      }
    }
    logsForRun(runId: $runId, afterCursor: $cursor, limit: $limit) {
      ... on EventConnection {
        events {
          ... on MessageEvent {
            runId
          }
          ...RunDagsterRunEventFragment
        }
        cursor
      }
      ... on PythonError {
        message
        stack
      }
    }
  }

  ${RUN_DAGSTER_RUN_EVENT_FRAGMENT}
`;
