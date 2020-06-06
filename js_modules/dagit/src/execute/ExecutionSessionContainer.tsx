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
  CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT,
  responseToYamlValidationResult
} from "../configeditor/ConfigEditorUtils";

import { ConfigEditorRunConfigSchemaFragment } from "../configeditor/types/ConfigEditorRunConfigSchemaFragment";
import {
  PreviewConfigQuery,
  PreviewConfigQueryVariables
} from "./types/PreviewConfigQuery";
import {
  ExecutionSessionContainerFragment,
  ExecutionSessionContainerFragment_InvalidSubsetError
} from "./types/ExecutionSessionContainerFragment";
import {
  ExecutionSessionContainerRunConfigSchemaFragment,
  ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError
} from "./types/ExecutionSessionContainerRunConfigSchemaFragment";
import { PipelineDetailsFragment } from "./types/PipelineDetailsFragment";
import { ConfigEditorHelp } from "./ConfigEditorHelp";
import { PipelineExecutionButtonGroup } from "./PipelineExecutionButtonGroup";
import { TagContainer, TagEditor } from "./TagEditor";
import { ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results_tags } from "./types/ConfigPartitionsQuery";
import { ShortcutHandler } from "../ShortcutHandler";
import ApolloClient from "apollo-client";
import { PipelineSelector } from "../types/globalTypes";

type PipelineTag = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results_tags;

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;

interface IExecutionSessionContainerProps {
  data: IStorageData;
  onSaveSession: (changes: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  pipelineOrError: ExecutionSessionContainerFragment;
  runConfigSchemaOrError:
    | ExecutionSessionContainerRunConfigSchemaFragment
    | undefined;
  currentSession: IExecutionSession;
  pipelineSelector: PipelineSelector;
}

interface IExecutionSessionContainerState {
  preview: PreviewConfigQuery | null;
  previewedDocument: object | null;

  editorHelpContext: ConfigEditorHelpContext | null;
  showWhitespace: boolean;
  tagEditorOpen: boolean;
}

export type SubsetError =
  | ExecutionSessionContainerFragment_InvalidSubsetError
  | undefined;

export type ModeNotFoundError =
  | ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError
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
    RunConfigSchemaOrErrorFragment: gql`
      fragment ExecutionSessionContainerRunConfigSchemaFragment on RunConfigSchemaOrError {
        __typename
        ... on RunConfigSchema {
          ...ConfigEditorRunConfigSchemaFragment
        }
        ... on ModeNotFoundError {
          message
        }
      }
      ${CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT}
    `
  };

  state: IExecutionSessionContainerState = {
    preview: null,
    previewedDocument: null,

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
      runConfigYaml: config
    });
  };

  onsolidSelectionChange = (
    solidSelection: string[] | null,
    solidSelectionQuery: string | null
  ) => {
    this.props.onSaveSession({
      solidSelection,
      solidSelectionQuery
    });
  };

  onModeChange = (mode: string) => {
    this.props.onSaveSession({ mode });
  };

  buildExecutionVariables = () => {
    const { currentSession, pipelineSelector } = this.props;
    const pipeline = this.getPipeline();
    if (!pipeline || !currentSession || !currentSession.mode) return;
    const tags = currentSession.tags || [];
    let runConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      runConfigData = yaml.parse(currentSession.runConfigYaml) || {};
    } catch (err) {
      alert(YAML_SYNTAX_INVALID);
      return;
    }

    return {
      executionParams: {
        runConfigData,
        selector: pipelineSelector,
        mode: currentSession.mode,
        executionMetadata: {
          tags: [
            ...tags.map(tag => ({ key: tag.key, value: tag.value })),
            // pass solid selection query via tags
            // clean up https://github.com/dagster-io/dagster/issues/2495
            ...(currentSession.solidSelectionQuery
              ? [
                  {
                    key: "dagster/solid_selection",
                    value: currentSession.solidSelectionQuery
                  }
                ]
              : []),
            ...(currentSession?.base?.["presetName"]
              ? [
                  {
                    key: "dagster/preset_name",
                    value: currentSession?.base?.["presetName"]
                  }
                ]
              : [])
          ]
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
  getRunConfigSchema = (): ConfigEditorRunConfigSchemaFragment | undefined => {
    const obj = this.props.runConfigSchemaOrError;
    if (obj && obj.__typename === "RunConfigSchema") {
      return obj;
    }
    return undefined;
  };

  getModeError = (): ModeNotFoundError => {
    const obj = this.props.runConfigSchemaOrError;
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

  checkConfig = async (client: ApolloClient<any>, configJSON: object) => {
    const { currentSession, pipelineSelector } = this.props;

    const { data } = await client.query<
      PreviewConfigQuery,
      PreviewConfigQueryVariables
    >({
      fetchPolicy: "no-cache",
      query: PREVIEW_CONFIG_QUERY,
      variables: {
        runConfigData: configJSON,
        pipeline: pipelineSelector,
        mode: currentSession.mode || "default"
      }
    });

    if (this.mounted) {
      this.setState({
        preview: data,
        previewedDocument: configJSON
      });
    }

    return responseToYamlValidationResult(
      configJSON,
      data.isPipelineConfigValid
    );
  };

  openTagEditor = () => this.setState({ tagEditorOpen: true });
  closeTagEditor = () => this.setState({ tagEditorOpen: false });

  render() {
    const { currentSession, onCreateSession, onSaveSession } = this.props;
    const {
      preview,
      previewedDocument,
      editorHelpContext,
      showWhitespace,
      tagEditorOpen
    } = this.state;
    const runConfigSchema = this.getRunConfigSchema();
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
              <ConfigEditorConfigPicker
                pipelineName={pipeline.name}
                base={currentSession.base}
                solidSelection={currentSession.solidSelection}
                onCreateSession={onCreateSession}
                onSaveSession={onSaveSession}
              />
              <div style={{ width: 5 }} />
              <SolidSelector
                serverProvidedSubsetError={subsetError}
                pipelineName={pipeline.name}
                value={currentSession.solidSelection || null}
                query={currentSession.solidSelectionQuery || null}
                onChange={this.onsolidSelectionChange}
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
                allInnerTypes={runConfigSchema?.allConfigTypes || []}
              />
              <ApolloConsumer>
                {client => (
                  <ConfigEditor
                    ref={this.editor}
                    readOnly={false}
                    runConfigSchema={runConfigSchema}
                    configCode={currentSession.runConfigYaml}
                    onConfigChange={this.onConfigChange}
                    onHelpContextChange={next => {
                      if (!isHelpContextEqual(editorHelpContext, next)) {
                        this.setState({ editorHelpContext: next });
                      }
                    }}
                    showWhitespace={showWhitespace}
                    checkConfig={async configJSON => {
                      return await this.checkConfig(client, configJSON);
                    }}
                  />
                )}
              </ApolloConsumer>
            </ConfigEditorContainer>
          </>
        }
        second={
          runConfigSchema ? (
            <RunPreview
              document={previewedDocument}
              plan={preview ? preview.executionPlanOrError : null}
              validation={preview ? preview.isPipelineConfigValid : null}
              runConfigSchema={runConfigSchema}
              onHighlightPath={path =>
                this.editor.current?.moveCursorToPath(path)
              }
              actions={
                <PipelineExecutionButtonGroup
                  pipelineName={pipeline.name}
                  getVariables={this.buildExecutionVariables}
                  disabled={
                    preview?.executionPlanOrError?.__typename !==
                    "ExecutionPlan"
                  }
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
    $pipeline: PipelineSelector!
    $runConfigData: RunConfigData!
    $mode: String!
  ) {
    isPipelineConfigValid(
      pipeline: $pipeline
      runConfigData: $runConfigData
      mode: $mode
    ) {
      ...ConfigEditorValidationFragment
      ...RunPreviewValidationFragment
    }
    executionPlanOrError(
      pipeline: $pipeline
      runConfigData: $runConfigData
      mode: $mode
    ) {
      ...RunPreviewExecutionPlanOrErrorFragment
    }
  }
  ${RunPreview.fragments.RunPreviewValidationFragment}
  ${RunPreview.fragments.RunPreviewExecutionPlanOrErrorFragment}
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
