import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components";
import { Button, Colors, Spinner } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ApolloConsumer, Mutation, MutationFn } from "react-apollo";

import TabBar from "./TabBar";
import ExecutionStartButton from "./ExecutionStartButton";
import { handleStartExecutionResult } from "../runs/RunUtils";
import { RunPreview } from "./RunPreview";
import { PanelDivider } from "../PanelDivider";
import SolidSelector from "./SolidSelector";
import ConfigEditor from "../configeditor/ConfigEditor";
import ConfigEditorPresetsPicker from "./ConfigEditorPresetsPicker";
import ConfigEditorModePicker from "./ConfigEditorModePicker";
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
  pipelineName: string;
  currentSession: IExecutionSession;
}

interface IPipelineExecutionContainerState {
  editorVW: number;
  preview: PreviewConfigQuery | null;
  showWhitespace: boolean;
}

export default class PipelineExecutionContainer extends React.Component<
  IPipelineExecutionContainerProps,
  IPipelineExecutionContainerState
> {
  static fragments = {
    PipelineExecutionContainerFragment: gql`
      fragment PipelineExecutionContainerFragment on Pipeline {
        name
        modes {
          name
          description
        }
        ...ConfigEditorPipelineFragment
      }
      ${CONFIG_EDITOR_PIPELINE_FRAGMENT}
    `
  };

  state: IPipelineExecutionContainerState = {
    editorVW: 75,
    preview: null,
    showWhitespace: true
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
    const { pipeline } = this.props;
    if (!pipeline) return;
  }

  onConfigChange = (config: any) => {
    this.onSaveSession(this.props.currentSession.key, {
      environmentConfigYaml: config
    });
  };

  onSolidSubsetChange = (solidSubset: string[] | null) => {
    this.onSaveSession(this.props.currentSession.key, { solidSubset });
  };

  onModeChange = (mode: string) => {
    this.onSaveSession(this.props.currentSession.key, { mode });
  };

  onSelectSession = (session: string) => {
    this.props.onSave(applySelectSession(this.props.data, session));
  };

  onSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    this.props.onSave(applyChangesToSession(this.props.data, session, changes));
  };

  onCreateSession = (initial?: Partial<IExecutionSession>) => {
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
    handleStartExecutionResult(pipeline.name, result, {
      openInNewWindow: true
    });
  };

  buildExecutionVariables = () => {
    const { currentSession, pipeline } = this.props;
    if (!currentSession || !pipeline || !currentSession.mode) return;

    let environmentConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      console.log(currentSession.environmentConfigYaml);
      environmentConfigData =
        yaml.parse(currentSession.environmentConfigYaml) || {};
    } catch (err) {
      alert(YAML_SYNTAX_INVALID);
      return;
    }

    return {
      executionParams: {
        environmentConfigData,
        selector: {
          name: pipeline.name,
          solidSubset: currentSession.solidSubset
        },
        mode: currentSession.mode
      }
    };
  };

  render() {
    const { currentSession, pipeline, pipelineName } = this.props;
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
              {pipeline &&
                (!this.state.preview ? (
                  <Spinner size={17} />
                ) : (
                  <ExecutionStartButton
                    title="Start Execution"
                    icon={IconNames.PLAY}
                    onClick={() => this.onExecute(startPipelineExecution)}
                  />
                ))}
            </TabBar>
          )}
        </Mutation>
        {currentSession ? (
          <PipelineExecutionWrapper>
            <Split width={this.state.editorVW} style={{ flexShrink: 0 }}>
              <ConfigEditorPresetInsertionContainer className="bp3-dark">
                {pipeline && (
                  <ConfigEditorPresetsPicker
                    pipelineName={pipeline.name}
                    solidSubset={currentSession.solidSubset}
                    onCreateSession={this.onCreateSession}
                  />
                )}
              </ConfigEditorPresetInsertionContainer>
              <ApolloConsumer>
                {client => (
                  <ConfigEditor
                    readOnly={false}
                    pipeline={pipeline}
                    configCode={currentSession.environmentConfigYaml}
                    onConfigChange={this.onConfigChange}
                    showWhitespace={this.state.showWhitespace}
                    checkConfig={async environmentConfigData => {
                      if (!pipeline) return { isValid: true };
                      if (!currentSession.mode) {
                        return {
                          isValid: false,
                          errors: [
                            // FIXME this should be specific -- we should have an enumerated
                            // validation error when there is no mode provided
                            {
                              message: "Must specify a mode",
                              path: ["root"],
                              reason: "MISSING_REQUIRED_FIELD"
                            }
                          ]
                        };
                      }
                      const { data } = await client.query<
                        PreviewConfigQuery,
                        PreviewConfigQueryVariables
                      >({
                        fetchPolicy: "no-cache",
                        query: PREVIEW_CONFIG_QUERY,
                        variables: {
                          environmentConfigData,
                          pipeline: {
                            name: pipeline.name,
                            solidSubset: currentSession.solidSubset
                          },
                          mode: currentSession.mode || "default"
                        }
                      });

                      this.setState({ preview: data });

                      return responseToValidationResult(
                        environmentConfigData,
                        data.isPipelineConfigValid
                      );
                    }}
                  />
                )}
              </ApolloConsumer>
              <SessionSettingsFooter className="bp3-dark">
                {pipeline && (
                  <>
                    <SolidSelector
                      pipelineName={pipelineName}
                      value={currentSession.solidSubset || null}
                      onChange={this.onSolidSubsetChange}
                    />

                    <ConfigEditorModePicker
                      pipeline={pipeline}
                      onModeChange={this.onModeChange}
                      modeName={currentSession.mode}
                    />

                    <Button
                      icon="paragraph"
                      small={true}
                      active={this.state.showWhitespace}
                      style={{ marginLeft: "auto" }}
                      onClick={() =>
                        this.setState({
                          showWhitespace: !this.state.showWhitespace
                        })
                      }
                    />
                  </>
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
  mutation StartPipelineExecution($executionParams: ExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
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
    $environmentConfigData: EnvironmentConfigData!
    $mode: String!
  ) {
    isPipelineConfigValid(
      pipeline: $pipeline
      environmentConfigData: $environmentConfigData
      mode: $mode
    ) {
      ...ConfigEditorValidationFragment
      ...RunPreviewConfigValidationFragment
    }
    executionPlan(
      pipeline: $pipeline
      environmentConfigData: $environmentConfigData
      mode: $mode
    ) {
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

const ConfigEditorPresetInsertionContainer = styled.div`
  display: inline-block;
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
`;
