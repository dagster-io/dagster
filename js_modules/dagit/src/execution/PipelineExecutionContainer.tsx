import * as React from "react";
import gql from "graphql-tag";
import { ApolloClient } from "apollo-client";
import { DataProxy } from "apollo-cache";
import produce from "immer";
import { Mutation, FetchResult } from "react-apollo";
import * as yaml from "yaml";
import RunBar from "./RunBar";
import RunSubscriptionProvider from "./RunSubscriptionProvider";
import { titleForRun } from "./ExecutionUtils";

import {
  applyChangesToSession,
  applySelectSession,
  applyRemoveSession,
  applyCreateSession,
  IStorageData,
  IExecutionSession,
  IExecutionSessionChanges
} from "../LocalStorage";
import PipelineExecution from "./PipelineExecution";
import {
  PipelineExecutionContainerFragment,
  PipelineExecutionContainerFragment_runs
} from "./types/PipelineExecutionContainerFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IPipelineExecutionContainerProps {
  client: ApolloClient<any>;
  pipeline: PipelineExecutionContainerFragment;
  currentSession: IExecutionSession;
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
          ...RunBarRunFragment
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
      ${RunBar.fragments.RunBarRunFragment}
    `
  };

  handleSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  handleSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    this.props.onSave(applyChangesToSession(this.props.data, session, changes));
  };

  handleCreateSession = (initial?: IExecutionSessionChanges) => {
    this.props.onSave(applyCreateSession(this.props.data, initial));
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

      window.alert(message);
    }
  };

  buildExecutionVariables = () => {
    const { currentSession, pipeline } = this.props;

    let config = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      config = yaml.parse(currentSession.config) || {};
    } catch (err) {
      alert(YAML_SYNTAX_INVALID);
      return;
    }

    return {
      config,
      pipeline: {
        name: pipeline.name,
        solidSubset: currentSession.solidSubset
      }
    };
  };

  render() {
    const { currentSession, pipeline } = this.props;
    const currentRun =
      pipeline.runs.find(r => currentSession.runId === r.runId) || null;

    return (
      <Mutation<StartPipelineExecution, StartPipelineExecutionVariables>
        mutation={START_PIPELINE_EXECUTION_MUTATION}
        key={pipeline.name}
        update={this.handleExecutionResult}
      >
        {(startPipelineExecution, { loading }) => (
          <>
            <RunSubscriptionProvider
              client={this.props.client}
              pipeline={pipeline}
              run={currentRun}
            />
            <RunBar
              executing={currentRun ? isRunExecuting(currentRun) : false}
              runs={pipeline.runs}
              sessions={this.props.data.sessions}
              currentSession={currentSession}
              onSelectSession={this.handleSelectSession}
              onCreateSession={this.handleCreateSession}
              onRemoveSession={this.handleRemoveSession}
              onSaveSession={this.handleSaveSession}
              onExecute={async event => {
                if (!currentSession) return;

                const variables = this.buildExecutionVariables();
                if (!variables) return;

                const useNewTab =
                  !currentSession.runId || event.altKey || event.metaKey;
                const result = await startPipelineExecution({ variables });
                if (
                  result &&
                  result.data &&
                  result.data.startPipelineExecution.__typename ===
                    "StartPipelineExecutionSuccess"
                ) {
                  const run = result.data.startPipelineExecution.run;

                  if (useNewTab) {
                    this.handleCreateSession({
                      ...currentSession,
                      name: titleForRun(run),
                      runId: run.runId
                    });
                  } else {
                    this.handleSaveSession(currentSession.key, {
                      configChangedSinceRun: false,
                      name: titleForRun(run),
                      runId: run.runId
                    });
                  }
                }
              }}
            />
            <PipelineExecution
              pipeline={this.props.pipeline}
              currentRun={currentRun}
              currentSession={this.props.currentSession}
              onSaveSession={this.handleSaveSession}
            />
          </>
        )}
      </Mutation>
    );
  }
}

const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartPipelineExecution(
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
  ) {
    startPipelineExecution(pipeline: $pipeline, config: $config) {
      __typename

      ... on StartPipelineExecutionSuccess {
        run {
          runId
          status
          ...RunBarRunFragment
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
  ${RunBar.fragments.RunBarRunFragment}
  ${PipelineExecution.fragments.PipelineExecutionPipelineRunFragment}
`;

function isRunExecuting(
  activeRun: PipelineExecutionContainerFragment_runs | null
) {
  if (!activeRun) return false;
  const start = activeRun.logs.nodes.find(
    l => l.__typename === "PipelineProcessStartEvent"
  );
  const end = activeRun.logs.nodes.find(
    l =>
      l.__typename === "PipelineSuccessEvent" ||
      l.__typename === "PipelineFailureEvent"
  );
  return start !== null && end == null;
}
