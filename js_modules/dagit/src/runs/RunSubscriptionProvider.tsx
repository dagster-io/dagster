import * as React from "react";
import gql from "graphql-tag";
import { ApolloClient } from "apollo-client";
import produce from "immer";
import { PipelineRunStatus } from "../types/globalTypes";

import { PipelineRun } from "./PipelineRun";
import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";
import { PipelineRunLogsUpdateFragment } from "./types/PipelineRunLogsUpdateFragment";

interface IRunSubscriptionProviderProps {
  client: ApolloClient<any>;
  runId: string;
  runLogCursor: string;
}

export default class RunSubscriptionProvider extends React.Component<
  IRunSubscriptionProviderProps
> {
  _subscriptionRunId: string | null = null;
  _subscription: ZenObservable.Subscription;

  componentDidMount() {
    this.subscribeToRun();
  }

  componentDidUpdate() {
    this.subscribeToRun();
  }

  componentWillUnmount() {
    this.unsubscribeFromRuns();
  }

  subscribeToRun() {
    if (this._subscriptionRunId === this.props.runId) return;

    if (this._subscription) this._subscription.unsubscribe();

    const observable = this.props.client.subscribe({
      query: PIPELINE_RUN_LOGS_SUBSCRIPTION,
      variables: {
        runId: this.props.runId,
        after: this.props.runLogCursor
      }
    });

    this._subscriptionRunId = this.props.runId;
    this._subscription = observable.subscribe({
      next: msg => {
        this.handleNewMessages(msg.data);
      }
    });
  }

  unsubscribeFromRuns() {
    this._subscription.unsubscribe();
    this._subscriptionRunId = null;
  }

  handleNewMessages = (result: PipelineRunLogsSubscription) => {
    if (
      result.pipelineRunLogs.__typename ==
      "PipelineRunLogsSubscriptionMissingRunIdFailure"
    ) {
      return;
    }
    const messages = result.pipelineRunLogs.messages;
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
  };

  render() {
    return false;
  }
}

const PIPELINE_RUN_LOGS_UPDATE_FRAGMENT = gql`
  fragment PipelineRunLogsUpdateFragment on PipelineRun {
    runId
    status
    ...PipelineRunFragment
    logs {
      nodes {
        ...PipelineRunPipelineRunEventFragment
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunFragment}
  ${PipelineRun.fragments.PipelineRunPipelineRunEventFragment}
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
          }
          ...PipelineRunPipelineRunEventFragment
        }
      }
      ... on PipelineRunLogsSubscriptionMissingRunIdFailure {
        missingRunId
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunPipelineRunEventFragment}
`;
