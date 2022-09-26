import {gql, useApolloClient, useQuery} from '@apollo/client';
import {TokenizingFieldValue} from '@dagster-io/ui';
import throttle from 'lodash/throttle';
import * as React from 'react';

import {WebSocketContext} from '../app/WebSocketProvider';
import {RunStatus} from '../types/globalTypes';

import {LogLevelCounts} from './LogsToolbar';
import {RunFragments} from './RunFragments';
import {logNodeLevel} from './logNodeLevel';
import {LogNode} from './types';
import {PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess} from './types/PipelineRunLogsSubscription';
import {PipelineRunLogsSubscriptionStatusFragment} from './types/PipelineRunLogsSubscriptionStatusFragment';
import {RunDagsterRunEventFragment} from './types/RunDagsterRunEventFragment';
import {RunLogsQuery, RunLogsQueryVariables} from './types/RunLogsQuery';
import {
  usePipelineRunLogsSubscription,
  usePipelineRunLogsSubscriptionWorker,
} from './usePipelineRunLogsSubscription';

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
  allNodes: LogNode[];
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
const QUERY_LOG_LIMIT = 10000;

type State = {
  nodes: LogNode[];
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
      const nodes = [...state.nodes, ...queuedNodes];
      const counts = {...state.counts};
      queuedNodes.forEach((node) => {
        const level = logNodeLevel(node);
        counts[level]++;
      });
      return {nodes, counts, loading: action.hasMore, cursor: action.cursor};
    }
    case 'set-cursor':
      return {...state, cursor: action.cursor};
    case 'reset':
      return {nodes: [], counts: emptyCounts, cursor: null, loading: true};
    default:
      return state;
  }
};

const initialState: State = {
  nodes: [],
  counts: emptyCounts,
  cursor: null,
  loading: true,
};

const useLogsProviderWithSubscription = (runId: string) => {
  const client = useApolloClient();
  const queue = React.useRef<
    PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess[]
  >([]);
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const syncPipelineStatusToApolloCache = React.useCallback(
    (status: RunStatus) => {
      const local = client.readFragment<PipelineRunLogsSubscriptionStatusFragment>({
        fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
        fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
        id: `Run:${runId}`,
      });

      if (local) {
        const toWrite = {...local, status};
        if (
          status === RunStatus.FAILURE ||
          status === RunStatus.SUCCESS ||
          status === RunStatus.STARTING ||
          status === RunStatus.CANCELING ||
          status === RunStatus.CANCELED
        ) {
          toWrite.canTerminate = false;
        }

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
      const lastLog = queuedLogs[queuedLogs.length - 1];
      const hasMore = lastLog.hasMorePastEvents;
      const cursor = lastLog.cursor;

      dispatch({type: 'append', queued: queuedMessages, hasMore, cursor});

      // If we're still loading past events, don't sync to the cache -- event chunks could
      // give us `status` values that don't match the actual state of the run.
      if (!hasMore) {
        const nextPipelineStatus = pipelineStatusFromMessages(queuedMessages);
        if (nextPipelineStatus) {
          syncPipelineStatusToApolloCache(nextPipelineStatus);
        }
      }
    }, BATCH_INTERVAL);
  }, [syncPipelineStatusToApolloCache]);

  const {nodes, counts, cursor, loading} = state;

  const useHook = new URLSearchParams(window.location.search).get('worker')
    ? usePipelineRunLogsSubscriptionWorker
    : usePipelineRunLogsSubscription;

  console.log({useHook});

  useHook(
    {runId, cursor},
    React.useCallback(
      (logs: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess) => {
        // Maintain a queue of messages as they arrive, and call the throttled setter.
        queue.current = [...queue.current, logs];
        // Wait until end of animation frame to call throttled set nodes
        // otherwise we wont end up batching anything if rendering takes
        // longer than the BATCH_INTERVAL
        requestAnimationFrame(throttledSetNodes);
      },
      [throttledSetNodes],
    ),
  );

  return React.useMemo(
    () => (nodes !== null ? {allNodes: nodes, counts, loading} : {allNodes: [], counts, loading}),
    [counts, loading, nodes],
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
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {counts, cursor, nodes} = state;

  const {stopPolling, startPolling} = useQuery<RunLogsQuery, RunLogsQueryVariables>(
    RUN_LOGS_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      variables: {runId, cursor, limit: QUERY_LOG_LIMIT},
      pollInterval: POLL_INTERVAL,
      onCompleted: (data: RunLogsQuery) => {
        // We have to stop polling in order to update the `after` value.
        stopPolling();

        if (
          data?.pipelineRunOrError.__typename !== 'Run' ||
          data?.logsForRun.__typename !== 'EventConnection'
        ) {
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

        if (hasMore) {
          startPolling(POLL_INTERVAL);
        }
      },
    },
  );

  return (
    <>
      {children(
        nodes !== null && nodes.length > 0
          ? {allNodes: nodes, counts, loading: false}
          : {allNodes: [], counts, loading: true},
      )}
    </>
  );
};

export const LogsProvider: React.FC<LogsProviderProps> = (props) => {
  const {children, runId} = props;
  const {availability, disabled} = React.useContext(WebSocketContext);

  // if disabled, drop to query variant immediately
  if (availability === 'unavailable' || disabled) {
    return <LogsProviderWithQuery runId={runId}>{children}</LogsProviderWithQuery>;
  }

  if (availability === 'attempting-to-connect') {
    return <>{children({allNodes: [], counts: emptyCounts, loading: true})}</>;
  }

  return <LogsProviderWithSubscription runId={runId}>{children}</LogsProviderWithSubscription>;
};

const PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT = gql`
  fragment PipelineRunLogsSubscriptionStatusFragment on Run {
    id
    runId
    status
    canTerminate
  }
`;

const RUN_LOGS_QUERY = gql`
  query RunLogsQuery($runId: ID!, $cursor: String, $limit: Int) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        runId
        status
        canTerminate
      }
    }
    logsForRun(runId: $runId, afterCursor: $cursor, limit: $limit) {
      ... on EventConnection {
        events {
          __typename
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
  ${RunFragments.RunDagsterRunEventFragment}
`;
