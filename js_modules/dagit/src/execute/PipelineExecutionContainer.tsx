import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Spinner } from "@blueprintjs/core";
import { ApolloConsumer, Mutation, MutationFn } from "react-apollo";

import TabBar from "./TabBar";
import { showCustomAlert } from "../CustomAlertProvider";
import ExecutionStartButton from "./ExecutionStartButton";
import { RunPreview } from "./RunPreview";
import { PanelDivider } from "../PanelDivider";
import SolidSelector from "./SolidSelector";
import ConfigEditor from "../configeditor/ConfigEditor";
import {
  applyChangesToSession,
  applySelectSession,
  applyRemoveSession,
  applyCreateSession,
  IStorageData,
  IExecutionSession,
  IExecutionSessionChanges
} from "../LocalStorage";
import {
  CONFIG_EDITOR_PIPELINE_FRAGMENT,
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  responseToValidationResult
} from "../configeditor/ConfigEditorUtils";

import {
  PreviewConfigQuery,
  PreviewConfigQueryVariables
} from "./types/PreviewConfigQuery";
import { PipelineExecutionContainerFragment } from "./types/PipelineExecutionContainerFragment";
import {
  StartPipelineExecution,
  StartPipelineExecutionVariables
} from "./types/StartPipelineExecution";

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IPipelineExecutionContainerProps {
  data: IStorageData;
  onSave: (data: IStorageData) => void;
  pipeline?: PipelineExecutionContainerFragment;
  currentSession: IExecutionSession;
}

interface IPipelineExecutionContainerState {
  editorVW: number;
  preview: PreviewConfigQuery | null;
}

export default class PipelineExecutionContainer extends React.Component<
  IPipelineExecutionContainerProps,
  IPipelineExecutionContainerState
> {
  static fragments = {
    PipelineExecutionContainerFragment: gql`
      fragment PipelineExecutionContainerFragment on Pipeline {
        name
        environmentType {
          key
        }
        ...ConfigEditorPipelineFragment
      }
      ${CONFIG_EDITOR_PIPELINE_FRAGMENT}
    `
  };

  state: IPipelineExecutionContainerState = {
    editorVW: 75,
    preview: null
  };

  mounted = false;

  componentDidMount() {
    this.mounted = true;
    this.ensureSessionStateValid();
  }

  componentDidUpdate() {
    this.ensureSessionStateValid();
  }

  componentWillUnmount() {
    this.mounted = false;
  }

  ensureSessionStateValid() {
    const { currentSession, pipeline } = this.props;
    if (!pipeline) return;
  }

  onConfigChange = (config: any) => {
    this.onSaveSession(this.props.currentSession.key, { config });
  };

  onSolidSubsetChange = (solidSubset: string[] | null) => {
    this.onSaveSession(this.props.currentSession.key, { solidSubset });
  };

  onSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  onSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    this.props.onSave(applyChangesToSession(this.props.data, session, changes));
  };

  onCreateSession = (initial?: IExecutionSessionChanges) => {
    this.props.onSave(applyCreateSession(this.props.data, initial));
  };

  onRemoveSession = (session: string) => {
    this.props.onSave(applyRemoveSession(this.props.data, session));
  };

  onExecute = async (
    startPipelineExecution: MutationFn<
      StartPipelineExecution,
      StartPipelineExecutionVariables
    >
  ) => {
    const { pipeline } = this.props;
    const { preview } = this.state;

    if (!pipeline || !preview) {
      alert(
        "Dagit is still retrieving pipeline info. Please try again in a moment."
      );
      return;
    }

    const variables = this.buildExecutionVariables();
    if (!variables) return;

    const result = await startPipelineExecution({ variables });
    if (!result || !result.data) {
      alert("No data was returned.");
      return;
    }

    const obj = result.data.startPipelineExecution;

    if (obj.__typename === "StartPipelineExecutionSuccess") {
      window.open(`/${pipeline.name}/runs/${obj.run.runId}`, "_blank");
    } else {
      let message = `${
        pipeline.name
      } cannot not be executed with the provided config.`;

      if ("errors" in obj) {
        message += ` Please fix the following errors:\n\n${obj.errors
          .map(error => error.message)
          .join("\n\n")}`;
      }

      showCustomAlert({ message });
    }
  };

  buildExecutionVariables = () => {
    const { currentSession, pipeline } = this.props;
    if (!currentSession || !pipeline) return;

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
    const { preview } = this.state;

    return (
      <>
        <Mutation<StartPipelineExecution, StartPipelineExecutionVariables>
          mutation={START_PIPELINE_EXECUTION_MUTATION}
        >
          {startPipelineExecution => (
            <TabBar
              sessions={this.props.data.sessions}
              currentSession={currentSession}
              onSelectSession={this.onSelectSession}
              onCreateSession={this.onCreateSession}
              onRemoveSession={this.onRemoveSession}
              onSaveSession={this.onSaveSession}
            >
              {!this.state.preview ? (
                <Spinner size={17} />
              ) : (
                <ExecutionStartButton
                  onClick={() => this.onExecute(startPipelineExecution)}
                />
              )}
            </TabBar>
          )}
        </Mutation>
        {currentSession ? (
          <PipelineExecutionWrapper>
            <Split width={this.state.editorVW} style={{ flexShrink: 0 }}>
              <ApolloConsumer>
                {client => (
                  <ConfigEditor
                    readOnly={false}
                    pipeline={pipeline}
                    configCode={currentSession.config}
                    onConfigChange={this.onConfigChange}
                    checkConfig={async config => {
                      if (!pipeline) return { isValid: true };

                      const { data } = await client.query<
                        PreviewConfigQuery,
                        PreviewConfigQueryVariables
                      >({
                        fetchPolicy: "no-cache",
                        query: PREVIEW_CONFIG_QUERY,
                        variables: {
                          config,
                          pipeline: {
                            name: pipeline.name,
                            solidSubset: currentSession.solidSubset
                          }
                        }
                      });

                      this.setState({ preview: data });

                      return responseToValidationResult(
                        config,
                        data.isPipelineConfigValid
                      );
                    }}
                  />
                )}
              </ApolloConsumer>
              <SessionSettingsFooter className="bp3-dark">
                {!pipeline ? (
                  <span />
                ) : (
                  <SolidSelector
                    pipelineName={pipeline.name}
                    value={currentSession.solidSubset || null}
                    onChange={this.onSolidSubsetChange}
                  />
                )}
              </SessionSettingsFooter>
            </Split>
            <PanelDivider
              axis="horizontal"
              onMove={(vw: number) => this.setState({ editorVW: vw })}
            />
            <Split>
              {preview ? (
                <RunPreview
                  plan={preview.executionPlan}
                  validation={preview.isPipelineConfigValid}
                />
              ) : (
                <RunPreview />
              )}
            </Split>
          </PipelineExecutionWrapper>
        ) : (
          <span />
        )}
      </>
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

const PREVIEW_CONFIG_QUERY = gql`
  query PreviewConfigQuery(
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
  ) {
    isPipelineConfigValid(pipeline: $pipeline, config: $config) {
      ...ConfigEditorValidationFragment
      ...RunPreviewConfigValidationFragment
    }
    executionPlan(pipeline: $pipeline, config: $config) {
      ...RunPreviewExecutionPlanResultFragment
    }
  }
  ${RunPreview.fragments.RunPreviewConfigValidationFragment}
  ${RunPreview.fragments.RunPreviewExecutionPlanResultFragment}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

const PipelineExecutionWrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  position: absolute;
  padding-top: 100px;
`;

const SessionSettingsFooter = styled.div`
  color: white;
  display: flex;
  border-top: 1px solid ${Colors.DARK_GRAY5};
  background-color: ${Colors.DARK_GRAY2};
  align-items: center;
  height: 47px;
  padding: 8px;
}
`;

const Split = styled.div<{ width?: number }>`
  ${props => (props.width ? `width: ${props.width}vw` : `flex: 1`)};
  position: relative;
  flex-direction: column;
  display: flex;
`;
