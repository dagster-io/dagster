import {ApolloClient, gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {DirectGraphQLSubscription} from '../app/DirectGraphQLSubscription';
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

interface LogsProviderProps {
  websocketURI: string;
  client: ApolloClient<any>;
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

const LogsProviderWithSubscription = (props: LogsProviderProps) => {
  // todo dish: Get WS info from context.
  const {websocketURI, client, runId, children} = props;
  const [nodes, setNodes] = React.useState<Nodes | null>(null);

  React.useEffect(() => {
    setNodes([]);
  }, [runId]);

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

  const onHandleMessages = React.useCallback(
    (messages: PipelineRunLogsSubscription[], isFirstResponse: boolean) => {
      const toAppend: RunPipelineRunEventFragment[] = [];

      let nextPipelineStatus: PipelineRunStatus | null = null;
      for (const msg of messages) {
        if (msg.pipelineRunLogs.__typename === 'PipelineRunLogsSubscriptionFailure') {
          break;
        }

        // append the nodes to our local array and give each of them a unique key
        // so we can change the row indexes they're displayed at and still track their
        // sizes, etc.
        toAppend.push(...msg.pipelineRunLogs.messages);

        // look for changes to the pipeline's overall run status and sync that to apollo
        for (const {__typename} of msg.pipelineRunLogs.messages) {
          if (__typename === 'PipelineStartEvent') {
            nextPipelineStatus = PipelineRunStatus.STARTED;
          } else if (__typename === 'PipelineEnqueuedEvent') {
            nextPipelineStatus = PipelineRunStatus.QUEUED;
          } else if (__typename === 'PipelineStartingEvent') {
            nextPipelineStatus = PipelineRunStatus.STARTING;
          } else if (__typename === 'PipelineCancelingEvent') {
            nextPipelineStatus = PipelineRunStatus.CANCELING;
          } else if (__typename === 'PipelineCanceledEvent') {
            nextPipelineStatus = PipelineRunStatus.CANCELED;
          } else if (__typename === 'PipelineSuccessEvent') {
            nextPipelineStatus = PipelineRunStatus.SUCCESS;
          } else if (__typename === 'PipelineFailureEvent') {
            nextPipelineStatus = PipelineRunStatus.FAILURE;
          }
        }
      }

      if (nextPipelineStatus) {
        syncPipelineStatusToApolloCache(nextPipelineStatus);
      }

      setNodes((current) => {
        // Note: if the socket says this is the first response, it may be becacuse the connection
        // was dropped and re-opened, so we reset our local state to an empty array.
        const existing = isFirstResponse ? [] : [...(current || [])];
        return [...existing, ...toAppend].map((m, idx) => ({...m, clientsideKey: `csk${idx}`}));
      });
    },
    [syncPipelineStatusToApolloCache],
  );

  React.useEffect(() => {
    const subscription = new DirectGraphQLSubscription<PipelineRunLogsSubscription>(
      websocketURI,
      PIPELINE_RUN_LOGS_SUBSCRIPTION,
      {runId: runId, after: null},
      onHandleMessages,
      () => {}, // https://github.com/dagster-io/dagster/issues/2151
    );

    return () => {
      subscription.close();
    };
  }, [onHandleMessages, runId, websocketURI]);

  return (
    <>
      {children(nodes !== null ? {allNodes: nodes, loading: false} : {allNodes: [], loading: true})}
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
  const {client, children, runId, websocketURI} = props;
  const websocketAvailability = useWebsocketAvailability();

  if (websocketAvailability === 'attempting-to-connect') {
    return <>{children({allNodes: [], loading: true})}</>;
  }

  if (websocketAvailability === 'error') {
    return <LogsProviderWithQuery runId={runId}>{children}</LogsProviderWithQuery>;
  }

  return (
    <LogsProviderWithSubscription runId={runId} websocketURI={websocketURI} client={client}>
      {children}
    </LogsProviderWithSubscription>
  );
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
