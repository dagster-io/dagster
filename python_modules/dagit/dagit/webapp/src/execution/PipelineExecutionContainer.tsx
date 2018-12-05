import * as React from "react";
import gql from "graphql-tag";
import ZenObservable from "zen-observable-ts";
import { ApolloClient } from "apollo-client";
import { DataProxy } from "apollo-cache";
import produce from "immer";
import { Mutation, FetchResult } from "react-apollo";
import {
  applyConfigToSession,
  applySelectSession,
  applyNameToSession,
  applyRemoveSession,
  applyCreateSession,
  IStorageData
} from "../LocalStorage";
import PipelineExecution from "./PipelineExecution";
import {
  PipelineExecutionContainerFragment,
  PipelineExecutionContainerFragment_runs,
  PipelineRunStatus
} from "./types/PipelineExecutionContainerFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";
import {
  PipelineRunLogsSubscription,
  PipelineRunLogsSubscriptionVariables
} from "./types/PipelineRunLogsSubscription";
import { PipelineRunLogsUpdateFragment } from "./types/PipelineRunLogsUpdateFragment";

interface IPipelineExecutionContainerProps {
  client: ApolloClient<any>;
  pipeline: PipelineExecutionContainerFragment;
  data: IStorageData;
  onSave: (data: IStorageData) => void;
}

export default class PipelineExecutionContainer extends React.Component<
  IPipelineExecutionContainerProps
> {
  static fragments = {
    PipelineExecutionContainerFragment: gql`
      fragment PipelineExecutionContainerFragment on Pipeline {
        name
        runs {
          runId
          status
          ...PipelineExecutionPipelineRunFragment
          logs {
            pageInfo {
              lastCursor
            }
          }
        }
        ...PipelineExecutionCodeEditorFragment
      }

      ${PipelineExecution.fragments.PipelineExecutionCodeEditorFragment}
      ${PipelineExecution.fragments.PipelineExecutionPipelineRunFragment}
    `
  };

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
    const validRuns = this.props.pipeline.runs.filter(({ status }) => {
      return (
        status === PipelineRunStatus.NOT_STARTED ||
        status === PipelineRunStatus.STARTED
      );
    });
    // const validRunIds = new Set(validRuns.map(({ runId }) => runId));
    // const subscribedRunIds = new Set(Object.keys(this._subscriptions));
    // for (const staleRunId of []) {
    //   this._subscriptions[staleRunId].unsubscribe();
    // }

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
        next: this.handleNewMessage
      });
    });
  }

  unsubscribeFromRuns() {
    Object.keys(this._subscriptions).forEach(key => {
      this._subscriptions[key].unsubscribe();
    });
  }

  handleSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  handleSaveSession = (session: string, config: any) => {
    this.props.onSave(applyConfigToSession(this.props.data, session, config));
  };

  handleRenameSession = (session: string, title: string) => {
    this.props.onSave(applyNameToSession(this.props.data, session, title));
  };

  handleCreateSession = () => {
    this.props.onSave(applyCreateSession(this.props.data));
  };

  handleRemoveSession = (session: string) => {
    this.props.onSave(applyRemoveSession(this.props.data, session));
  };

  handleExecutionResult = (
    proxy: DataProxy,
    result: FetchResult<StartPipelineExecution, StartPipelineExecutionVariables>
  ) => {
    if (
      result.data &&
      result.data.startPipelineExecution.__typename ===
        "StartPipelineExecutionSuccess"
    ) {
      const run = result.data.startPipelineExecution.run;
      const id = `Pipeline.${this.props.pipeline.name}`;
      const existingData: PipelineExecutionContainerFragment | null = proxy.readFragment(
        {
          id,
          fragmentName: "PipelineExecutionContainerFragment",
          fragment:
            PipelineExecutionContainer.fragments
              .PipelineExecutionContainerFragment
        }
      );
      if (existingData) {
        const newData = produce(existingData, draftData => {
          draftData.runs.push(run);
        });
        proxy.writeFragment({
          id,
          fragmentName: "PipelineExecutionContainerFragment",
          fragment:
            PipelineExecutionContainer.fragments
              .PipelineExecutionContainerFragment,
          data: newData
        });
      }
    } else {
      // XXX(freiksenet): STUB
      alert("Error in config!");
    }
  };

  handleNewMessage = (
    result: FetchResult<
      PipelineRunLogsSubscription,
      PipelineRunLogsSubscriptionVariables
    >
  ) => {
    const data = result.data;
    if (data) {
      const id = `PipelineRun.${data.pipelineRunLogs.run.runId}`;
      const existingData: PipelineRunLogsUpdateFragment | null = this.props.client.readFragment(
        {
          fragmentName: "PipelineRunLogsUpdateFragment",
          fragment: PIPELINE_RUN_LOGS_UPDATE_FRAGMENT,
          id
        }
      );
      if (existingData) {
        const newData = produce(existingData, draftData => {
          draftData.logs.nodes.push(data.pipelineRunLogs);
        });
        this.props.client.writeFragment({
          fragmentName: "PipelineRunLogsUpdateFragment",
          fragment: PIPELINE_RUN_LOGS_UPDATE_FRAGMENT,
          id,
          data: newData
        });
      }
    }
  };

  render() {
    let activeRun: PipelineExecutionContainerFragment_runs | null = null;
    if (this.props.pipeline.runs.length > 0) {
      activeRun = this.props.pipeline.runs[this.props.pipeline.runs.length - 1];
    }
    return (
      <Mutation<StartPipelineExecution, StartPipelineExecutionVariables>
        mutation={START_PIPELINE_EXECUTION_MUTATION}
        key={this.props.pipeline.name}
        update={this.handleExecutionResult}
      >
        {(startPipelineExecution, { loading }) => {
          return (
            <PipelineExecution
              pipeline={this.props.pipeline}
              activeRun={activeRun}
              sessions={this.props.data.sessions}
              currentSession={this.props.data.sessions[this.props.data.current]}
              isExecuting={loading}
              onSelectSession={this.handleSelectSession}
              onRenameSession={this.handleRenameSession}
              onSaveSession={this.handleSaveSession}
              onCreateSession={this.handleCreateSession}
              onRemoveSession={this.handleRemoveSession}
              onExecute={config =>
                startPipelineExecution({
                  variables: {
                    executionParams: {
                      pipelineName: this.props.pipeline.name,
                      config
                    }
                  }
                })
              }
            />
          );
        }}
      </Mutation>
    );
  }
}

const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartPipelineExecution($executionParams: PipelineExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
      __typename

      ... on StartPipelineExecutionSuccess {
        run {
          runId
          status
          ...PipelineExecutionPipelineRunFragment
          logs {
            pageInfo {
              lastCursor
            }
          }
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineConfigValidationInvalid {
        errors {
          message
        }
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunFragment}
`;

const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $after: Cursor) {
    pipelineRunLogs(runId: $runId, after: $after) {
      ... on MessageEvent {
        run {
          runId
        }
        ...PipelineExecutionPipelineRunEventFragment
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunEventFragment}
`;

const PIPELINE_RUN_LOGS_UPDATE_FRAGMENT = gql`
  fragment PipelineRunLogsUpdateFragment on PipelineRun {
    runId
    logs {
      nodes {
        ...PipelineExecutionPipelineRunEventFragment
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunEventFragment}
`;
