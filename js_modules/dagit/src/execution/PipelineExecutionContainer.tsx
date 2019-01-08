import * as React from "react";
import gql from "graphql-tag";
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
import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";
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
        ...PipelineExecutionPipelineFragment
      }

      ${PipelineExecution.fragments.PipelineExecutionPipelineFragment}
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

  handleSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  handleSaveSession = (session: string, config: string) => {
    this.props.onSave(applyConfigToSession(this.props.data, session, config));
  };

  handleRenameSession = (session: string, title: string) => {
    this.props.onSave(applyNameToSession(this.props.data, session, title));
  };

  handleCreateSession = (config: string) => {
    this.props.onSave(applyCreateSession(this.props.data, config));
  };

  handleRemoveSession = (session: string) => {
    this.props.onSave(applyRemoveSession(this.props.data, session));
  };

  handleExecutionResult = (
    proxy: DataProxy,
    result: FetchResult<StartPipelineExecution, StartPipelineExecutionVariables>
  ) => {
    if (!result.data) {
      alert("No data was returned.");
      return;
    }

    const execution = result.data.startPipelineExecution;

    if (execution.__typename === "StartPipelineExecutionSuccess") {
      const run = execution.run;
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
      let message = `${
        this.props.pipeline.name
      } cannot not be executed with the provided config.`;

      if ("errors" in execution) {
        message += ` Please fix the following errors:\n\n${execution.errors
          .map(error => error.message)
          .join("\n\n")}`;
      }

      alert(message);
    }
  };

  handleNewMessages = (result: PipelineRunLogsSubscription) => {
    const runId = result.pipelineRunLogs.messages[0].run.runId;
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
        result.pipelineRunLogs.messages.forEach(message => {
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
      messages {
        ... on MessageEvent {
          run {
            runId
          }
          ...PipelineExecutionPipelineRunEventFragment
        }
      }
    }
  }

  ${PipelineExecution.fragments.PipelineExecutionPipelineRunEventFragment}
`;

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
