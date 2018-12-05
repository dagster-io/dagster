import * as React from "react";
import gql from "graphql-tag";
import { DataProxy } from "apollo-cache";
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
  PipelineExecutionContainerFragment_runs
} from "./types/PipelineExecutionContainerFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";

interface IPipelineExecutionContainerProps {
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
        }
        ...PipelineExecutionFragment
      }

      ${PipelineExecution.fragments.PipelineExecutionFragment}
    `
  };

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
    } else {
      // XXX(freiksenet): STUB
      alert("Error in config!");
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
`;
