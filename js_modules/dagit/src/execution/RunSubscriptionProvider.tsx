import * as React from "react";
import gql from "graphql-tag";
import { ApolloClient } from "apollo-client";
import produce from "immer";
import { PipelineRunStatus } from "../types/globalTypes";

import PipelineExecution from "./PipelineExecution";
import {
  PipelineExecutionContainerFragment,
  PipelineExecutionContainerFragment_runs
} from "./types/PipelineExecutionContainerFragment";
import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";
import { PipelineRunLogsUpdateFragment } from "./types/PipelineRunLogsUpdateFragment";

interface IRunSubscriptionProviderProps {
  client: ApolloClient<any>;
  pipeline: PipelineExecutionContainerFragment;
  run: PipelineExecutionContainerFragment_runs | null;
}

export default class RunSubscriptionProvider extends React.Component<
  IRunSubscriptionProviderProps
> {
  componentDidMount() {
    this.subscribeToRuns();
  }

  componentDidUpdate() {
    this.subscribeToRuns();
  }

  componentWillUnmount() {
    this.unsubscribeFromRuns();
  }

  _subscriptions: {
    [runId: string]: ZenObservable.Subscription;
  } = {};

  subscribeToRuns() {
    const validRuns = this.props.run ? [this.props.run] : [];
    const validRunIds = new Set(validRuns.map(({ runId }) => runId));
    const subscribedRunIds = new Set(Object.keys(this._subscriptions));
    subscribedRunIds.forEach(runId => {
      if (!validRunIds.has(runId)) {
        this._subscriptions[runId].unsubscribe();
        delete this._subscriptions[runId];
      }
    });

    validRuns.forEach(run => {
      if (this._subscriptions[run.runId]) {
        return;
      }
      const observable = this.props.client.subscribe({
        query: PIPELINE_RUN_LOGS_SUBSCRIPTION,
        variables: {
          runId: run.runId,
          after: run.logs.pageInfo.lastCursor
        }
      });

      this._subscriptions[run.runId] = observable.subscribe({
        next: msg => {
          this.handleNewMessages(msg.data);
        }
      });
    });
  }

  unsubscribeFromRuns() {
    Object.keys(this._subscriptions).forEach(runId => {
      this._subscriptions[runId].unsubscribe();
      delete this._subscriptions[runId];
    });
  }

  handleNewMessages = (result: PipelineRunLogsSubscription) => {
    if (result.pipelineRunLogs.__typename == 'PipelineRunLogsSubscriptionMissingRunIdFailure') {
      return;
    } else if (result.pipelineRunLogs.__typename == 'PipelineRunLogsSubscriptionSuccess') {
      const messages = result.pipelineRunLogs.messages
      const runId = messages[0].run.runId;
      const id = `PipelineRun.${runId}`;

      let localData: PipelineRunLogsUpdateFragment | null = this.props.client.readFragment(
        {
          fragmentName: "PipelineRunLogsUpdateFragment",
          fragment: PIPELINE_RUN_LOGS_UPDATE_FRAGMENT,
          id
        }
      );
      if (localData === null) {
        return;
      }
      localData = produce(
        localData as PipelineRunLogsUpdateFragment,
        draftData => {
          messages.forEach(message => {
            draftData.logs.nodes.push(message);
            if (message.__typename === "PipelineProcessStartEvent") {
              draftData.status = PipelineRunStatus.STARTED;
            } else if (message.__typename === "PipelineSuccessEvent") {
              draftData.status = PipelineRunStatus.SUCCESS;
            } else if (message.__typename === "PipelineFailureEvent") {
              draftData.status = PipelineRunStatus.FAILURE;
            }
          });
        }
      );

      this.props.client.writeFragment({
        fragmentName: "PipelineRunLogsUpdateFragment",
        fragment: PIPELINE_RUN_LOGS_UPDATE_FRAGMENT,
        id,
        data: localData
      });
    }
  };

  render() {
    return false;
  }
}

const PIPELINE_RUN_LOGS_UPDATE_FRAGMENT = gql`
  fragment PipelineRunLogsUpdateFragment on PipelineRun {
    runId
    status
    logs {
      nodes {
        ...PipelineExecutionPipelineRunEventFragment
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunEventFragment}
`;

const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $after: Cursor) {
    pipelineRunLogs(runId: $runId, after: $after) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            run {
              runId
            }
            ...PipelineExecutionPipelineRunEventFragment
          }
        }
      }
      ... on PipelineRunLogsSubscriptionMissingRunIdFailure {
        missingRunId
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunEventFragment}
`;
