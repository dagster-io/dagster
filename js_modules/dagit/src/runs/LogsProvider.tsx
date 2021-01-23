import {ApolloClient, gql} from '@apollo/client';
import * as React from 'react';

import {DirectGraphQLSubscription} from 'src/app/DirectGraphQLSubscription';
import {RunFragments} from 'src/runs/RunFragments';
import {PipelineRunLogsSubscription} from 'src/runs/types/PipelineRunLogsSubscription';
import {PipelineRunLogsSubscriptionStatusFragment} from 'src/runs/types/PipelineRunLogsSubscriptionStatusFragment';
import {RunPipelineRunEventFragment} from 'src/runs/types/RunPipelineRunEventFragment';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {TokenizingFieldValue} from 'src/ui/TokenizingField';

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
  allNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  loading: boolean;
}

interface LogsProviderProps {
  client: ApolloClient<any>;
  runId: string;
  children: (result: LogsProviderLogs) => React.ReactChild;
}

interface LogsProviderState {
  nodes: (RunPipelineRunEventFragment & {clientsideKey: string})[] | null;
}

export class LogsProvider extends React.Component<LogsProviderProps, LogsProviderState> {
  state: LogsProviderState = {
    nodes: null,
  };

  _subscription: DirectGraphQLSubscription<PipelineRunLogsSubscription>;

  componentDidMount() {
    this.subscribeToRun();
  }

  componentDidUpdate(prevProps: LogsProviderProps) {
    if (prevProps.runId !== this.props.runId) {
      this.subscribeToRun();
    }
  }

  componentWillUnmount() {
    this.unsubscribeFromRun();
  }

  subscribeToRun() {
    const {runId} = this.props;

    if (this._subscription) {
      this.unsubscribeFromRun();
      this.setState({nodes: []});
    }

    if (!runId) {
      return;
    }

    this._subscription = new DirectGraphQLSubscription<PipelineRunLogsSubscription>(
      PIPELINE_RUN_LOGS_SUBSCRIPTION,
      {runId: runId, after: null},
      this.onHandleMessages,
      () => {}, // https://github.com/dagster-io/dagster/issues/2151
    );
  }

  unsubscribeFromRun() {
    if (this._subscription) {
      this._subscription.close();
    }
  }

  onHandleMessages = (messages: PipelineRunLogsSubscription[], isFirstResponse: boolean) => {
    // Note: if the socket says this is the first response, it may be becacuse the connection
    // was dropped and re-opened, so we reset our local state to an empty array.
    const nextNodes = isFirstResponse ? [] : [...(this.state.nodes || [])];

    let nextPipelineStatus: PipelineRunStatus | null = null;
    for (const msg of messages) {
      if (msg.pipelineRunLogs.__typename === 'PipelineRunLogsSubscriptionFailure') {
        break;
      }

      // append the nodes to our local array and give each of them a unique key
      // so we can change the row indexes they're displayed at and still track their
      // sizes, etc.
      nextNodes.push(
        ...msg.pipelineRunLogs.messages.map((m, idx) =>
          Object.assign(m, {clientsideKey: `csk${nextNodes.length + idx}`}),
        ),
      );

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
        } else if (
          __typename === 'PipelineFailureEvent' ||
          __typename === 'PipelineInitFailureEvent'
        ) {
          nextPipelineStatus = PipelineRunStatus.FAILURE;
        }
      }
    }

    if (nextPipelineStatus) {
      this.syncPipelineStatusToApolloCache(nextPipelineStatus);
    }
    this.setState({nodes: nextNodes});
  };

  syncPipelineStatusToApolloCache(status: PipelineRunStatus) {
    const local = this.props.client.readFragment<PipelineRunLogsSubscriptionStatusFragment>({
      fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
      fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
      id: `PipelineRun.${this.props.runId}`,
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
      this.props.client.writeFragment({
        fragmentName: 'PipelineRunLogsSubscriptionStatusFragment',
        fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
        id: `PipelineRun.${this.props.runId}`,
        data: toWrite,
      });
    }
  }

  render() {
    const {nodes} = this.state;

    return this.props.children(
      nodes !== null ? {allNodes: nodes, loading: false} : {allNodes: [], loading: true},
    );
  }
}

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
