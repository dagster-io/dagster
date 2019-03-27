import * as React from "react";
import gql from "graphql-tag";
import { Mutation } from "react-apollo";
import * as yaml from "yaml";
import TabBar from "./TabBar";
import { showCustomAlert } from "../CustomAlertProvider";

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
import { PipelineExecutionContainerFragment } from "./types/PipelineExecutionContainerFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IPipelineExecutionContainerProps {
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
        ...PipelineExecutionPipelineFragment
      }

      ${PipelineExecution.fragments.PipelineExecutionPipelineFragment}
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
    return (
      <Mutation<StartPipelineExecution, StartPipelineExecutionVariables>
        key={pipeline.name}
        mutation={START_PIPELINE_EXECUTION_MUTATION}
      >
        {startPipelineExecution => (
          <>
            <TabBar
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

                const result = await startPipelineExecution({ variables });
                if (!result || !result.data) {
                  alert("No data was returned.");
                  return;
                }

                const obj = result.data.startPipelineExecution;

                if (obj.__typename === "StartPipelineExecutionSuccess") {
                  window.open(
                    `/${pipeline.name}/runs/${obj.run.runId}`,
                    "_blank"
                  );
                } else {
                  let message = `${
                    this.props.pipeline.name
                  } cannot not be executed with the provided config.`;

                  if ("errors" in obj) {
                    message += ` Please fix the following errors:\n\n${obj.errors
                      .map(error => error.message)
                      .join("\n\n")}`;
                  }

                  showCustomAlert({ message });
                }
              }}
            />
            <PipelineExecution
              pipeline={this.props.pipeline}
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
