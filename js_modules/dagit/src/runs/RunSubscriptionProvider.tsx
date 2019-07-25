import * as React from "react";
import gql from "graphql-tag";
import { ApolloClient } from "apollo-client";
import produce from "immer";
import { PipelineRunStatus } from "../types/globalTypes";

import {
  PIPELINE_RUN_LOGS_UPDATE_FRAGMENT,
  PIPELINE_RUN_LOGS_SUBSCRIPTION
} from "./PipelineRun";
import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";
import { PipelineRunLogsUpdateFragment } from "./types/PipelineRunLogsUpdateFragment";
import { RunSubscriptionPipelineRunFragment } from "./types/RunSubscriptionPipelineRunFragment";

interface IRunSubscriptionProviderProps {
  client: ApolloClient<any>;
  run: RunSubscriptionPipelineRunFragment;
}

export default class RunSubscriptionProvider extends React.Component<
  IRunSubscriptionProviderProps
> {
  static fragments = {
    RunSubscriptionPipelineRunFragment: gql`
      fragment RunSubscriptionPipelineRunFragment on PipelineRun {
        runId
        logs {
          pageInfo {
            lastCursor
          }
        }
      }
    `
  };

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
    const {
      runId,
      logs: {
        pageInfo: { lastCursor }
      }
    } = this.props.run;

    if (this._subscriptionRunId === runId) return;
    if (this._subscription) this._subscription.unsubscribe();

    const observable = this.props.client.subscribe({
      query: PIPELINE_RUN_LOGS_SUBSCRIPTION,
      variables: {
        runId: runId,
        after: lastCursor
      }
    });

    this._subscriptionRunId = runId;
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
      result.pipelineRunLogs.__typename ===
      "PipelineRunLogsSubscriptionMissingRunIdFailure"
    ) {
      return;
    }
    const messages = result.pipelineRunLogs.messages;
    const runId = messages[0].runId;
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
          } else if (
            message.__typename === "PipelineFailureEvent" ||
            message.__typename === "PipelineInitFailureEvent"
          ) {
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
