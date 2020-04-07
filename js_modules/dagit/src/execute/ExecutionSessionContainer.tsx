import * as React from "react";
import * as yaml from "yaml";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors, Button, Spinner } from "@blueprintjs/core";
import { ApolloConsumer } from "react-apollo";

import { RunPreview } from "./RunPreview";
import { SplitPanelContainer } from "../SplitPanelContainer";
import SolidSelector from "./SolidSelector";
import {
  ConfigEditor,
  ConfigEditorHelpContext,
  isHelpContextEqual
} from "../configeditor/ConfigEditor";
import { ConfigEditorConfigPicker } from "./ConfigEditorConfigPicker";
import { ConfigEditorModePicker } from "./ConfigEditorModePicker";
import { IStorageData, IExecutionSession } from "../LocalStorage";
import {
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  CONFIG_EDITOR_ENVIRONMENT_SCHEMA_FRAGMENT,
  responseToValidationResult
} from "../configeditor/ConfigEditorUtils";

import { ConfigEditorEnvironmentSchemaFragment } from "../configeditor/types/ConfigEditorEnvironmentSchemaFragment";
import {
  PreviewConfigQuery,
  PreviewConfigQueryVariables,
  PreviewConfigQuery_executionPlan
} from "./types/PreviewConfigQuery";
import {
  ExecutionSessionContainerFragment,
  ExecutionSessionContainerFragment_InvalidSubsetError
} from "./types/ExecutionSessionContainerFragment";
import {
  ExecutionSessionContainerEnvironmentSchemaFragment,
  ExecutionSessionContainerEnvironmentSchemaFragment_ModeNotFoundError
} from "./types/ExecutionSessionContainerEnvironmentSchemaFragment";
import { PipelineDetailsFragment } from "./types/PipelineDetailsFragment";
import { ConfigEditorHelp } from "./ConfigEditorHelp";
import { PipelineExecutionButtonGroup } from "./PipelineExecutionButtonGroup";
import { TagContainer, TagEditor } from "./TagEditor";
import { ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results_tags } from "./types/ConfigPartitionsQuery";
import { ShortcutHandler } from "../ShortcutHandler";
import { ValidationResult } from "../configeditor/codemirror-yaml/mode";

type PipelineTag = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results_tags;

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IExecutionSessionContainerProps {
  data: IStorageData;
  onSaveSession: (changes: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  pipelineOrError: ExecutionSessionContainerFragment;
  environmentSchemaOrError:
    | ExecutionSessionContainerEnvironmentSchemaFragment
    | undefined;
  currentSession: IExecutionSession;
}

interface IExecutionSessionContainerState {
  plan: PreviewConfigQuery_executionPlan | null;
  validationResult: ValidationResult | null;

  editorHelpContext: ConfigEditorHelpContext | null;
  showWhitespace: boolean;
  tagEditorOpen: boolean;
}

export type SubsetError =
  | ExecutionSessionContainerFragment_InvalidSubsetError
  | undefined;

export type ModeNotFoundError =
  | ExecutionSessionContainerEnvironmentSchemaFragment_ModeNotFoundError
  | undefined;

export default class ExecutionSessionContainer extends React.Component<
  IExecutionSessionContainerProps,
  IExecutionSessionContainerState
> {
  static fragments = {
    ExecutionSessionContainerFragment: gql`
      fragment ExecutionSessionContainerFragment on PipelineOrError {
        ...PipelineDetailsFragment
        ... on InvalidSubsetError {
          message
          pipeline {
            ...PipelineDetailsFragment
          }
        }
      }

      fragment PipelineDetailsFragment on Pipeline {
        name
        modes {
          name
          description
        }
        tags {
          key
          value
        }
      }
    `,
    EnvironmentSchemaOrErrorFragment: gql`
      fragment ExecutionSessionContainerEnvironmentSchemaFragment on EnvironmentSchemaOrError {
        __typename
        ... on EnvironmentSchema {
          ...ConfigEditorEnvironmentSchemaFragment
        }
        ... on ModeNotFoundError {
          message
        }
      }
      ${CONFIG_EDITOR_ENVIRONMENT_SCHEMA_FRAGMENT}
    `
  };

  state: IExecutionSessionContainerState = {
    plan: null,
    validationResult: null,

    showWhitespace: true,
    editorHelpContext: null,
    tagEditorOpen: false
  };

  editor = React.createRef<ConfigEditor>();

  mounted = false;

  componentDidMount() {
    this.mounted = true;
  }

  componentWillUnmount() {
    this.mounted = false;
  }

  onConfigChange = (config: any) => {
    this.props.onSaveSession({
      environmentConfigYaml: config
    });
  };

  onSolidSubsetChange = (
    solidSubset: string[] | null,
    solidSubsetQuery: string | null
  ) => {
    this.props.onSaveSession({
      solidSubset,
      solidSubsetQuery
    });
  };

  onModeChange = (mode: string) => {
    this.props.onSaveSession({ mode });
  };

  buildExecutionVariables = () => {
    const { currentSession } = this.props;
    const pipeline = this.getPipeline();
    if (!pipeline || !currentSession || !currentSession.mode) return;
    const tags = currentSession.tags || [];
    let environmentConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
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
        mode: currentSession.mode,
        executionMetadata: {
          tags: tags.map(tag => ({ key: tag.key, value: tag.value }))
        }
      }
    };
  };

  getPipeline = (): PipelineDetailsFragment => {
    const obj = this.props.pipelineOrError;
    if (obj.__typename === "Pipeline") {
      return obj;
    } else if (obj.__typename === "InvalidSubsetError") {
      return obj.pipeline;
    }
    throw new Error(`Recieved unexpected "${obj.__typename}"`);
  };

  // have this return an object with prebuilt index
  // https://github.com/dagster-io/dagster/issues/1966
  getEnvironmentSchema = ():
    | ConfigEditorEnvironmentSchemaFragment
    | undefined => {
    const obj = this.props.environmentSchemaOrError;
    if (obj && obj.__typename === "EnvironmentSchema") {
      return obj;
    }
    return undefined;
  };

  getModeError = (): ModeNotFoundError => {
    const obj = this.props.environmentSchemaOrError;
    if (obj && obj.__typename === "ModeNotFoundError") {
      return obj;
    }
    return undefined;
  };

  getSubsetError = (): SubsetError => {
    const obj = this.props.pipelineOrError;
    if (obj && obj.__typename === "InvalidSubsetError") {
      return obj;
    }
    return undefined;
  };

  saveTags = (tags: PipelineTag[]) => {
    const tagDict = {};
    const toSave: PipelineTag[] = [];
    tags.forEach((tag: PipelineTag) => {
      if (!(tag.key in tagDict)) {
        tagDict[tag.key] = tag.value;
        toSave.push(tag);
      }
    });
    this.props.onSaveSession({ tags: toSave });
  };

  openTagEditor = () => this.setState({ tagEditorOpen: true });
  closeTagEditor = () => this.setState({ tagEditorOpen: false });

  render() {
    const { currentSession, onCreateSession } = this.props;
    const {
      plan,
      validationResult,
      editorHelpContext,
      showWhitespace,
      tagEditorOpen
    } = this.state;
    const environmentSchema = this.getEnvironmentSchema();
    const subsetError = this.getSubsetError();
    const modeError = this.getModeError();
    const pipeline = this.getPipeline();

    const tags = currentSession.tags || pipeline.tags || [];
    return (
      <SplitPanelContainer
        axis={"vertical"}
        identifier={"execution"}
        firstMinSize={100}
        firstInitialPercent={75}
        first={
          <>
            <SessionSettingsBar>
              <SolidSelector
                subsetError={subsetError}
                pipelineName={pipeline.name}
                value={currentSession.solidSubset || null}
                query={currentSession.solidSubsetQuery || null}
                onChange={this.onSolidSubsetChange}
              />
              <div style={{ width: 5 }} />
              <ConfigEditorModePicker
                modes={pipeline.modes}
                modeError={modeError}
                onModeChange={this.onModeChange}
                modeName={currentSession.mode}
              />
              {tags.length || tagEditorOpen ? null : (
                <ShortcutHandler
                  shortcutLabel={"⌥T"}
                  shortcutFilter={e => e.keyCode === 84 && e.altKey}
                  onShortcut={this.openTagEditor}
                >
                  <TagEditorLink onClick={this.openTagEditor}>
                    + Add tags
                  </TagEditorLink>
                </ShortcutHandler>
              )}
              <TagEditor
                tags={tags}
                onChange={this.saveTags}
                open={tagEditorOpen}
                onRequestClose={this.closeTagEditor}
              />
            </SessionSettingsBar>
            {tags.length ? (
              <TagContainer tags={tags} onRequestEdit={this.openTagEditor} />
            ) : null}
            <ConfigEditorPresetInsertionContainer>
              {pipeline && (
                <ConfigEditorConfigPicker
                  pipelineName={pipeline.name}
                  solidSubset={currentSession.solidSubset}
                  onCreateSession={onCreateSession}
                />
              )}
            </ConfigEditorPresetInsertionContainer>
            <ConfigEditorDisplayOptionsContainer>
              <Button
                icon="paragraph"
                small={true}
                active={showWhitespace}
                style={{ marginLeft: "auto" }}
                onClick={() =>
                  this.setState({ showWhitespace: !showWhitespace })
                }
              />
            </ConfigEditorDisplayOptionsContainer>
            <ConfigEditorContainer>
              <ConfigEditorHelp
                context={editorHelpContext}
                allInnerTypes={environmentSchema?.allConfigTypes || []}
              />
              <ApolloConsumer>
                {client => (
                  <ConfigEditor
                    ref={this.editor}
                    readOnly={false}
                    environmentSchema={environmentSchema}
                    configCode={currentSession.environmentConfigYaml}
                    onConfigChange={this.onConfigChange}
                    onHelpContextChange={next => {
                      if (!isHelpContextEqual(editorHelpContext, next)) {
                        this.setState({ editorHelpContext: next });
                      }
                    }}
                    showWhitespace={showWhitespace}
                    checkConfig={async configJSON => {
                      if (!currentSession.mode || modeError) {
                        return {
                          isValid: false,
                          document: configJSON,
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
                          environmentConfigData: configJSON,
                          pipeline: {
                            name: pipeline.name,
                            solidSubset: currentSession.solidSubset
                          },
                          mode: currentSession.mode || "default"
                        }
                      });

                      const validationResult = responseToValidationResult(
                        configJSON,
                        data.isPipelineConfigValid
                      );

                      if (this.mounted) {
                        this.setState({
                          plan: data.executionPlan,
                          validationResult: validationResult
                        });
                      }

                      return validationResult;
                    }}
                  />
                )}
              </ApolloConsumer>
            </ConfigEditorContainer>
          </>
        }
        second={
          environmentSchema ? (
            <RunPreview
              plan={plan}
              environmentSchema={environmentSchema}
              validationResult={validationResult}
              onHighlightValidationError={error =>
                this.editor.current?.moveCursorToValidationError(error)
              }
              actions={
                <PipelineExecutionButtonGroup
                  pipelineName={pipeline.name}
                  getVariables={this.buildExecutionVariables}
                  disabled={plan?.__typename !== "ExecutionPlan"}
                />
              }
            />
          ) : (
            <div />
          )
        }
      />
    );
  }
}

interface ExecutionSessionContainerErrorProps {
  onSaveSession: (changes: Partial<IExecutionSession>) => void;
  currentSession: IExecutionSession;
}

export const ExecutionSessionContainerError: React.FunctionComponent<ExecutionSessionContainerErrorProps> = props => {
  return (
    <SplitPanelContainer
      axis={"vertical"}
      identifier={"execution"}
      firstInitialPercent={75}
      firstMinSize={100}
      first={
        <>
          <SessionSettingsBar>
            <Spinner size={20} />
          </SessionSettingsBar>
          {props.children}
        </>
      }
      second={<div />}
    />
  );
};

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
    }
    executionPlan(
      pipeline: $pipeline
      environmentConfigData: $environmentConfigData
      mode: $mode
    ) {
      ...RunPreviewExecutionPlanResultFragment
    }
  }
  ${RunPreview.fragments.RunPreviewExecutionPlanResultFragment}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

const SessionSettingsBar = styled.div`
  color: white;
  display: flex;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  background: ${Colors.WHITE};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;

const ConfigEditorPresetInsertionContainer = styled.div`
  display: inline-block;
  position: absolute;
  top: 8px;
  right: 12px;
  z-index: 10;
`;

const ConfigEditorDisplayOptionsContainer = styled.div`
  display: inline-block;
  position: absolute;
  bottom: 14px;
  right: 14px;
  z-index: 10;
`;

const ConfigEditorContainer = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1 1 0%;
`;
const TagEditorLink = styled.div`
  color: #666;
  cursor: pointer;
  margin-left: 15px;
  text-decoration: underline;
  &:hover {
    color: #aaa;
  }
`;
