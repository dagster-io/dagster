import * as React from 'react';
import * as yaml from 'yaml';
import gql from 'graphql-tag';
import styled from 'styled-components/macro';
import {Colors, Button, Spinner, NonIdealState} from '@blueprintjs/core';
import {ApolloConsumer} from 'react-apollo';
import ApolloClient from 'apollo-client';

import {RunPreview} from './RunPreview';
import {SplitPanelContainer, SecondPanelToggle} from '../SplitPanelContainer';
import SolidSelector from './SolidSelector';
import {
  ConfigEditor,
  ConfigEditorHelpContext,
  isHelpContextEqual,
} from '../configeditor/ConfigEditor';
import {
  ConfigEditorConfigPicker,
  CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT,
  CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT,
} from './ConfigEditorConfigPicker';
import {ConfigEditorModePicker} from './ConfigEditorModePicker';
import {IStorageData, IExecutionSession} from '../LocalStorage';
import {
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT,
  responseToYamlValidationResult,
} from '../configeditor/ConfigEditorUtils';

import {ConfigEditorHelp} from './ConfigEditorHelp';
import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';
import {TagContainer, TagEditor} from './TagEditor';
import {ShortcutHandler} from '../ShortcutHandler';
import {PipelineSelector} from '../types/globalTypes';
import {PipelineRunTag} from '../LocalStorage';

import {PreviewConfigQuery, PreviewConfigQueryVariables} from './types/PreviewConfigQuery';
import {ExecutionSessionContainerPipelineFragment} from './types/ExecutionSessionContainerPipelineFragment';
import {
  ExecutionSessionContainerRunConfigSchemaFragment,
  ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError,
} from './types/ExecutionSessionContainerRunConfigSchemaFragment';
import {ExecutionSessionContainerPartitionSetsFragment} from './types/ExecutionSessionContainerPartitionSetsFragment';
import {ConfigEditorRunConfigSchemaFragment} from '../configeditor/types/ConfigEditorRunConfigSchemaFragment';
import {showCustomAlert} from '../CustomAlertProvider';

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;
const LOADING_PIPELINE = `Loading pipeline and partition sets...`;
const LOADING_CONFIG_FOR_PARTITION = `Generating configuration...`;
const LOADING_CONFIG_SCHEMA = `Loading config schema...`;
const LOADING_RUN_PREVIEW = `Checking config...`;

interface IExecutionSessionContainerProps {
  data: IStorageData;
  onSaveSession: (changes: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
  pipeline: ExecutionSessionContainerPipelineFragment;
  partitionSets: ExecutionSessionContainerPartitionSetsFragment;
  runConfigSchemaOrError?: ExecutionSessionContainerRunConfigSchemaFragment;
  currentSession: IExecutionSession;
  pipelineSelector: PipelineSelector;
}

interface IExecutionSessionContainerState {
  preview: PreviewConfigQuery | null;
  previewLoading: boolean;
  previewedDocument: object | null;

  configLoading: boolean;
  editorHelpContext: ConfigEditorHelpContext | null;
  showWhitespace: boolean;
  tagEditorOpen: boolean;
}

export type ModeNotFoundError =
  | ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError
  | undefined;

export default class ExecutionSessionContainer extends React.Component<
  IExecutionSessionContainerProps,
  IExecutionSessionContainerState
> {
  static fragments = {
    ExecutionSessionContainerPipelineFragment: gql`
      fragment ExecutionSessionContainerPipelineFragment on Pipeline {
        id
        ...ConfigEditorGeneratorPipelineFragment
        modes {
          name
          description
        }
      }
      ${CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT}
    `,
    ExecutionSessionContainerPartitionSetsFragment: gql`
      fragment ExecutionSessionContainerPartitionSetsFragment on PartitionSets {
        ...ConfigEditorGeneratorPartitionSetsFragment
      }
      ${CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT}
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
    `,
  };

  state: IExecutionSessionContainerState = {
    preview: null,
    previewLoading: false,
    previewedDocument: null,

    configLoading: false,
    showWhitespace: true,
    editorHelpContext: null,
    tagEditorOpen: false,
  };

  editor = React.createRef<ConfigEditor>();

  editorSplitPanelContainer = React.createRef<SplitPanelContainer>();

  mounted = false;

  previewCounter = 0;

  componentDidMount() {
    this.mounted = true;
  }

  componentWillUnmount() {
    this.mounted = false;
  }

  onConfigChange = (config: any) => {
    this.props.onSaveSession({
      runConfigYaml: config,
    });
  };

  onSolidSelectionChange = (
    solidSelection: string[] | null,
    solidSelectionQuery: string | null,
  ) => {
    this.props.onSaveSession({
      solidSelection,
      solidSelectionQuery,
    });
  };

  onModeChange = (mode: string) => {
    this.props.onSaveSession({mode});
  };

  onRemoveExtraPaths = (paths: string[]) => {
    const {currentSession} = this.props;

    function deletePropertyPath(obj: any, path: string) {
      const parts = path.split('.');

      // Here we iterate through the parts of the path to get to
      // the second to last nested object. This is so we can call `delete` using
      // this object and the last part of the path.
      for (let i = 0; i < parts.length - 1; i++) {
        obj = obj[parts[i]];
        if (typeof obj === 'undefined') {
          return;
        }
      }

      const lastKey = parts.pop();
      if (lastKey) {
        delete obj[lastKey];
      }
    }

    let runConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      runConfigData = yaml.parse(currentSession.runConfigYaml || '') || {};

      for (const path of paths) {
        deletePropertyPath(runConfigData, path);
      }

      const runConfigYaml = yaml.stringify(runConfigData);
      this.props.onSaveSession({runConfigYaml});
    } catch (err) {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }
  };

  buildExecutionVariables = () => {
    const {currentSession, pipelineSelector} = this.props;

    if (!currentSession || !currentSession.mode) {
      return;
    }
    const tags = currentSession.tags || [];
    let runConfigData = {};
    try {
      // Note: parsing `` returns null rather than an empty object,
      // which is preferable for representing empty config.
      runConfigData = yaml.parse(currentSession.runConfigYaml || '') || {};
    } catch (err) {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }

    return {
      executionParams: {
        runConfigData,
        selector: pipelineSelector,
        mode: currentSession.mode,
        executionMetadata: {
          tags: [
            ...tags.map((tag) => ({key: tag.key, value: tag.value})),
            // pass solid selection query via tags
            // clean up https://github.com/dagster-io/dagster/issues/2495
            ...(currentSession.solidSelectionQuery
              ? [
                  {
                    key: 'dagster/solid_selection',
                    value: currentSession.solidSelectionQuery,
                  },
                ]
              : []),
            ...(currentSession?.base?.['presetName']
              ? [
                  {
                    key: 'dagster/preset_name',
                    value: currentSession?.base?.['presetName'],
                  },
                ]
              : []),
          ],
        },
      },
    };
  };

  // have this return an object with prebuilt index
  // https://github.com/dagster-io/dagster/issues/1966
  getRunConfigSchema = (): ConfigEditorRunConfigSchemaFragment | undefined => {
    const obj = this.props.runConfigSchemaOrError;
    if (obj && obj.__typename === 'RunConfigSchema') {
      return obj;
    }
    return undefined;
  };

  getModeError = (): ModeNotFoundError => {
    const obj = this.props.runConfigSchemaOrError;
    if (obj && obj.__typename === 'ModeNotFoundError') {
      return obj;
    }
    return undefined;
  };

  saveTags = (tags: PipelineRunTag[]) => {
    const tagDict = {};
    const toSave: PipelineRunTag[] = [];
    tags.forEach((tag: PipelineRunTag) => {
      if (!(tag.key in tagDict)) {
        tagDict[tag.key] = tag.value;
        toSave.push(tag);
      }
    });
    this.props.onSaveSession({tags: toSave});
  };

  checkConfig = async (client: ApolloClient<any>, configJSON: object) => {
    const {currentSession, pipelineSelector} = this.props;

    // Another request to preview a newer document may be made while this request
    // is in flight, in which case completion of this async method should not set loading=false.
    this.previewCounter += 1;
    const currentPreviewCount = this.previewCounter;

    this.setState({previewLoading: true});

    const {data} = await client.query<PreviewConfigQuery, PreviewConfigQueryVariables>({
      fetchPolicy: 'no-cache',
      query: PREVIEW_CONFIG_QUERY,
      variables: {
        runConfigData: configJSON,
        pipeline: pipelineSelector,
        mode: currentSession.mode || 'default',
      },
    });

    if (this.mounted) {
      const isLatestRequest = currentPreviewCount === this.previewCounter;
      this.setState({
        preview: data,
        previewedDocument: configJSON,
        previewLoading: isLatestRequest ? false : this.state.previewLoading,
      });
    }

    return responseToYamlValidationResult(configJSON, data.isPipelineConfigValid);
  };

  openTagEditor = () => this.setState({tagEditorOpen: true});
  closeTagEditor = () => this.setState({tagEditorOpen: false});

  onConfigLoading = () => this.setState({configLoading: true});
  onConfigLoaded = () => this.setState({configLoading: false});

  render() {
    const {currentSession, onCreateSession, onSaveSession, partitionSets, pipeline} = this.props;
    const {
      preview,
      previewLoading,
      previewedDocument,
      configLoading,
      editorHelpContext,
      showWhitespace,
      tagEditorOpen,
    } = this.state;
    const runConfigSchema = this.getRunConfigSchema();
    const modeError = this.getModeError();

    const tags = currentSession.tags || [];
    return (
      <SplitPanelContainer
        axis={'vertical'}
        identifier={'execution'}
        firstMinSize={100}
        firstInitialPercent={75}
        first={
          <>
            <LoadingOverlay isLoading={configLoading} message={LOADING_CONFIG_FOR_PARTITION} />
            <SessionSettingsBar>
              <ConfigEditorConfigPicker
                pipeline={pipeline}
                partitionSets={partitionSets.results}
                base={currentSession.base}
                solidSelection={currentSession.solidSelection}
                onLoading={this.onConfigLoading}
                onLoaded={this.onConfigLoaded}
                onCreateSession={onCreateSession}
                onSaveSession={onSaveSession}
              />
              <SessionSettingsSpacer />
              <SolidSelector
                serverProvidedSubsetError={
                  preview?.isPipelineConfigValid.__typename === 'InvalidSubsetError'
                    ? preview.isPipelineConfigValid
                    : undefined
                }
                pipelineName={pipeline.name}
                value={currentSession.solidSelection || null}
                query={currentSession.solidSelectionQuery || null}
                onChange={this.onSolidSelectionChange}
              />
              <SessionSettingsSpacer />
              <ConfigEditorModePicker
                modes={pipeline.modes}
                modeError={modeError}
                onModeChange={this.onModeChange}
                modeName={currentSession.mode}
              />
              {tags.length || tagEditorOpen ? null : (
                <ShortcutHandler
                  shortcutLabel={'⌥T'}
                  shortcutFilter={(e) => e.keyCode === 84 && e.altKey}
                  onShortcut={this.openTagEditor}
                >
                  <TagEditorLink onClick={this.openTagEditor}>+ Add tags</TagEditorLink>
                </ShortcutHandler>
              )}
              <TagEditor
                tags={tags}
                onChange={this.saveTags}
                open={tagEditorOpen}
                onRequestClose={this.closeTagEditor}
              />
              <div style={{flex: 1}} />
              <Button
                icon="paragraph"
                small={true}
                active={showWhitespace}
                style={{marginLeft: 'auto'}}
                onClick={() => this.setState({showWhitespace: !showWhitespace})}
              />
              <SessionSettingsSpacer />
              <SecondPanelToggle axis="horizontal" container={this.editorSplitPanelContainer} />
            </SessionSettingsBar>
            {tags.length ? <TagContainer tags={tags} onRequestEdit={this.openTagEditor} /> : null}
            <SplitPanelContainer
              ref={this.editorSplitPanelContainer}
              axis="horizontal"
              identifier="execution-editor"
              firstMinSize={100}
              firstInitialPercent={70}
              first={
                <ApolloConsumer>
                  {(client) => (
                    <ConfigEditor
                      ref={this.editor}
                      readOnly={false}
                      runConfigSchema={runConfigSchema}
                      configCode={currentSession.runConfigYaml}
                      onConfigChange={this.onConfigChange}
                      onHelpContextChange={(next) => {
                        if (!isHelpContextEqual(editorHelpContext, next)) {
                          this.setState({editorHelpContext: next});
                        }
                      }}
                      showWhitespace={showWhitespace}
                      checkConfig={async (configJSON) => {
                        return await this.checkConfig(client, configJSON);
                      }}
                    />
                  )}
                </ApolloConsumer>
              }
              second={
                <ConfigEditorHelp
                  context={editorHelpContext}
                  allInnerTypes={runConfigSchema?.allConfigTypes || []}
                />
              }
            />
          </>
        }
        second={
          <>
            <LoadingOverlay
              isLoading={!runConfigSchema || previewLoading}
              message={!runConfigSchema ? LOADING_CONFIG_SCHEMA : LOADING_RUN_PREVIEW}
            />
            <RunPreview
              document={previewedDocument}
              validation={preview ? preview.isPipelineConfigValid : null}
              runConfigSchema={runConfigSchema}
              onHighlightPath={(path) => this.editor.current?.moveCursorToPath(path)}
              onRemoveExtraPaths={(paths) => this.onRemoveExtraPaths(paths)}
              actions={
                <LaunchRootExecutionButton
                  pipelineName={pipeline.name}
                  getVariables={this.buildExecutionVariables}
                  disabled={
                    preview?.isPipelineConfigValid?.__typename !== 'PipelineConfigValidationValid'
                  }
                />
              }
            />
          </>
        }
      />
    );
  }
}

// Normally we'd try to make the execution session container props optional and render these empty / error
// states in the same component, but it's a lot less complicated to render them separately here.

export const ExecutionSessionContainerError: React.FunctionComponent<NonIdealState['props']> = (
  props,
) => (
  <SplitPanelContainer
    axis={'vertical'}
    identifier={'execution'}
    firstInitialPercent={75}
    firstMinSize={100}
    first={
      <>
        <SessionSettingsBar>
          <Spinner size={20} />
        </SessionSettingsBar>
        <NonIdealState {...props} />
      </>
    }
    second={<div />}
  />
);

export const ExecutionSessionContainerLoading: React.FunctionComponent = () => (
  <SplitPanelContainer
    axis={'vertical'}
    identifier={'execution'}
    firstInitialPercent={75}
    firstMinSize={100}
    first={
      <>
        <LoadingOverlay isLoading message={LOADING_PIPELINE} />
        <SessionSettingsBar />
      </>
    }
    second={<LoadingOverlay isLoading message={'Loading pipeline and partition sets...'} />}
  />
);

const PREVIEW_CONFIG_QUERY = gql`
  query PreviewConfigQuery(
    $pipeline: PipelineSelector!
    $runConfigData: RunConfigData!
    $mode: String!
  ) {
    isPipelineConfigValid(pipeline: $pipeline, runConfigData: $runConfigData, mode: $mode) {
      ...ConfigEditorValidationFragment
      ...RunPreviewValidationFragment
    }
  }
  ${RunPreview.fragments.RunPreviewValidationFragment}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

const SessionSettingsBar = styled.div`
  color: white;
  display: flex;
  position: relative;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  background: ${Colors.WHITE};
  align-items: center;
  height: 47px;
  padding: 8px 10px;
`;

const LoadingOverlayContainer = styled.div<{isLoading: boolean}>`
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background-color: #fff;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: ${({isLoading}) => (isLoading ? '0.7' : '0')};
  transition: opacity 150ms linear;
  transition-delay: 300ms;
  pointer-events: none;
`;

const LoadingOverlay: React.FunctionComponent<{
  isLoading: boolean;
  message: string;
}> = ({isLoading, message}) => (
  <LoadingOverlayContainer isLoading={isLoading}>
    <Spinner size={24} />
    &nbsp;&nbsp;{message}
  </LoadingOverlayContainer>
);

const SessionSettingsSpacer = styled.div`
  width: 5px;
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
