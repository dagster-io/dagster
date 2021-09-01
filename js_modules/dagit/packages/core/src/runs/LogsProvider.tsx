import {gql, useApolloClient, useQuery, useSubscription} from '@apollo/client';
import throttle from 'lodash/throttle';
import * as React from 'react';

import {useWebsocketAvailability} from '../app/useWebsocketAvailability';
import {PipelineRunStatus} from '../types/globalTypes';
import {TokenizingFieldValue} from '../ui/TokenizingField';

import {RunFragments} from './RunFragments';
import {PipelineRunLogsSubscription} from './types/PipelineRunLogsSubscription';
import {PipelineRunLogsSubscriptionStatusFragment} from './types/PipelineRunLogsSubscriptionStatusFragment';
import {RunLogsQuery} from './types/RunLogsQuery';
import {RunPipelineRunEventFragment} from './types/RunPipelineRunEventFragment';

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

type LogNode = RunPipelineRunEventFragment & {clientsideKey: string};
type Nodes = LogNode[];

export interface LogsProviderLogs {
  allNodes: LogNode[];
  loading: boolean;
}

const pipelineStatusFromMessages = (messages: RunPipelineRunEventFragment[]) => {
  const reversed = [...messages].reverse();
  for (const message of reversed) {
    const {__typename} = message;
    switch (__typename) {
      case 'PipelineStartEvent':
        return PipelineRunStatus.STARTED;
      case 'PipelineEnqueuedEvent':
        return PipelineRunStatus.QUEUED;
      case 'PipelineStartingEvent':
        return PipelineRunStatus.STARTING;
      case 'PipelineCancelingEvent':
        return PipelineRunStatus.CANCELING;
      case 'PipelineCanceledEvent':
        return PipelineRunStatus.CANCELED;
      case 'PipelineSuccessEvent':
        return PipelineRunStatus.SUCCESS;
      case 'PipelineFailureEvent':
        return PipelineRunStatus.FAILURE;
    }
  }
  return null;
};

const BATCH_INTERVAL = 100;

const useLogsProviderWithSubscription = (runId: string) => {
  const client = useApolloClient();
  const queue = React.useRef<RunPipelineRunEventFragment[]>([]);
  const [nodes, setNodes] = React.useState<Nodes>(() => []);

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

  React.useEffect(() => {
    queue.current = [];
    setNodes([]);
  }, [runId]);

  // Batch the nodes together so they don't overwhelm the animation of the Gantt,
  // which depends on a bit of a timing delay to maintain smoothness.
  const throttledSetNodes = React.useMemo(() => {
    return throttle(() => {
      setNodes((current) => {
        if (queue.current.length) {
          const update = [...current, ...queue.current].map((m, idx) => ({
            ...m,
            clientsideKey: `csk${idx}`,
          }));
          queue.current = [];
          return update;
        }
        return current;
      });
    }, BATCH_INTERVAL);
  }, []);

  useSubscription<PipelineRunLogsSubscription>(PIPELINE_RUN_LOGS_SUBSCRIPTION, {
    fetchPolicy: 'no-cache',
    variables: {runId: runId, after: null},
    onSubscriptionData: ({subscriptionData}) => {
      const logs = subscriptionData.data?.pipelineRunLogs;
      if (!logs || logs.__typename === 'PipelineRunLogsSubscriptionFailure') {
        return;
      }

      const {messages} = logs;
      const nextPipelineStatus = pipelineStatusFromMessages(messages);
      if (nextPipelineStatus) {
        syncPipelineStatusToApolloCache(nextPipelineStatus);
      }

      // Maintain a queue of messages as they arrive, and call the throttled setter.
      queue.current = [...queue.current, ...messages];
      throttledSetNodes();
    },
  });

  return React.useMemo(
    () => (nodes !== null ? {allNodes: nodes, loading: false} : {allNodes: [], loading: true}),
    [nodes],
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
  const websocketAvailability = useWebsocketAvailability();

  if (websocketAvailability === 'attempting-to-connect') {
    return <>{children({allNodes: [], loading: true})}</>;
  }

  if (websocketAvailability === 'error') {
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
          ...RunPipelineRunEventFragment
        }
      }
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
    }
  }

  ${RunFragments.RunPipelineRunEventFragment}
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
          ...RunPipelineRunEventFragment
          __typename
        }
      }
    }
  }
  ${RunFragments.RunPipelineRunEventFragment}
`;
