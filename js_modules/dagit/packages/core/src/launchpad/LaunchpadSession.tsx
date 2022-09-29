import {gql, useApolloClient, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  ConfigEditor,
  ConfigEditorHelpContext,
  Group,
  Icon,
  SecondPanelToggle,
  SplitPanelContainer,
  isHelpContextEqual,
  ConfigEditorHelp,
  TextInput,
} from '@dagster-io/ui';
import merge from 'deepmerge';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';
import styled from 'styled-components/macro';
import * as yaml from 'yaml';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {
  IExecutionSession,
  IExecutionSessionChanges,
  PipelineRunTag,
  SessionBase,
} from '../app/ExecutionSessionStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {
  CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT,
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  responseToYamlValidationResult,
} from '../configeditor/ConfigEditorUtils';
import {DagsterTag} from '../runs/RunTag';
import {PipelineSelector, RepositorySelector} from '../types/globalTypes';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  ConfigEditorConfigPicker,
  CONFIG_PARTITION_SELECTION_QUERY,
} from './ConfigEditorConfigPicker';
import {ConfigEditorModePicker} from './ConfigEditorModePicker';
import {LaunchRootExecutionButton} from './LaunchRootExecutionButton';
import {LaunchpadType} from './LaunchpadRoot';
import {LoadingOverlay} from './LoadingOverlay';
import {OpSelector} from './OpSelector';
import {RunPreview, RUN_PREVIEW_VALIDATION_FRAGMENT} from './RunPreview';
import {SessionSettingsBar} from './SessionSettingsBar';
import {TagContainer, TagEditor} from './TagEditor';
import {scaffoldPipelineConfig} from './scaffoldType';
import {ConfigEditorGeneratorPipelineFragment_presets} from './types/ConfigEditorGeneratorPipelineFragment';
import {
  ConfigPartitionSelectionQuery,
  ConfigPartitionSelectionQueryVariables,
} from './types/ConfigPartitionSelectionQuery';
import {LaunchpadSessionPartitionSetsFragment} from './types/LaunchpadSessionPartitionSetsFragment';
import {LaunchpadSessionPipelineFragment} from './types/LaunchpadSessionPipelineFragment';
import {
  PipelineExecutionConfigSchemaQuery,
  PipelineExecutionConfigSchemaQueryVariables,
} from './types/PipelineExecutionConfigSchemaQuery';
import {PreviewConfigQuery, PreviewConfigQueryVariables} from './types/PreviewConfigQuery';

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;
const LOADING_CONFIG_FOR_PARTITION = `Generating configuration...`;
const LOADING_CONFIG_SCHEMA = `Loading config schema...`;
const LOADING_RUN_PREVIEW = `Checking config...`;

type Preset = ConfigEditorGeneratorPipelineFragment_presets;

interface LaunchpadSessionProps {
  session: IExecutionSession;
  onSave: (changes: IExecutionSessionChanges) => void;
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  initialExecutionSessionState?: Partial<IExecutionSession>;
}

interface ILaunchpadSessionState {
  preview: PreviewConfigQuery | null;
  previewLoading: boolean;
  previewedDocument: any | null;
  configLoading: boolean;
  editorHelpContext: ConfigEditorHelpContext | null;
  tagEditorOpen: boolean;
}

type Action =
  | {type: 'preview-loading'; payload: boolean}
  | {
      type: 'set-preview';
      payload: {
        preview: PreviewConfigQuery | null;
        previewLoading: boolean;
        previewedDocument: string | null;
      };
    }
  | {type: 'toggle-tag-editor'; payload: boolean}
  | {type: 'toggle-config-loading'; payload: boolean}
  | {type: 'set-editor-help-context'; payload: ConfigEditorHelpContext | null};

const reducer = (state: ILaunchpadSessionState, action: Action) => {
  switch (action.type) {
    case 'preview-loading':
      return {...state, previewLoading: action.payload};
    case 'set-preview': {
      const {preview, previewedDocument, previewLoading} = action.payload;
      return {
        ...state,
        preview,
        previewedDocument,
        previewLoading,
      };
    }
    case 'toggle-tag-editor':
      return {...state, tagEditorOpen: action.payload};
    case 'toggle-config-loading':
      return {...state, configLoading: action.payload};
    case 'set-editor-help-context':
      return {...state, editorHelpContext: action.payload};
    default:
      return state;
  }
};

const LaunchButtonContainer: React.FC<{launchpadType: LaunchpadType}> = ({
  launchpadType,
  children,
}) => {
  if (launchpadType === 'asset') {
    return (
      <Box
        flex={{direction: 'row'}}
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
        padding={{right: 12, vertical: 8}}
      >
        <div style={{flexGrow: 1}} />
        {children}
      </Box>
    );
  } else {
    // job
    return <div style={{position: 'absolute', bottom: 12, right: 12, zIndex: 1}}>{children}</div>;
  }
};

const initialState: ILaunchpadSessionState = {
  preview: null,
  previewLoading: false,
  previewedDocument: null,
  configLoading: false,
  editorHelpContext: null,
  tagEditorOpen: false,
};

const LaunchpadSession: React.FC<LaunchpadSessionProps> = (props) => {
  const {
    launchpadType,
    session: currentSession,
    onSave,
    partitionSets,
    pipeline,
    repoAddress,
  } = props;

  const client = useApolloClient();
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const mounted = React.useRef<boolean>(false);
  const editor = React.useRef<ConfigEditor | null>(null);
  const editorSplitPanelContainer = React.useRef<SplitPanelContainer | null>(null);
  const previewCounter = React.useRef(0);

  const {isJob} = pipeline;
  const tagsFromSession = React.useMemo(() => currentSession.tags || [], [currentSession]);

  const pipelineSelector: PipelineSelector = {
    ...repoAddressToSelector(repoAddress),
    pipelineName: pipeline.name,
    solidSelection: currentSession?.solidSelection || undefined,
  };

  const configResult = useQuery<
    PipelineExecutionConfigSchemaQuery,
    PipelineExecutionConfigSchemaQueryVariables
  >(PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY, {
    variables: {selector: pipelineSelector, mode: currentSession?.mode},
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
  });

  const configSchemaOrError = configResult?.data?.runConfigSchemaOrError;

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  });

  const onSaveSession = (changes: IExecutionSessionChanges) => {
    onSave(changes);
  };

  const onConfigChange = (config: any) => {
    onSaveSession({
      runConfigYaml: config,
    });
  };

  const onOpSelectionChange = (
    solidSelection: string[] | null,
    solidSelectionQuery: string | null,
  ) => {
    onSaveSession({
      solidSelection,
      solidSelectionQuery,
    });
  };

  const onFlattenGraphsChange = (flattenGraphs: boolean) => {
    onSaveSession({flattenGraphs});
  };

  const onModeChange = (mode: string) => {
    onSaveSession({mode});
  };

  const onRemoveExtraPaths = (paths: string[]) => {
    try {
      const runConfigData = yaml.parse(sanitizeConfigYamlString(currentSession.runConfigYaml));
      for (const path of paths) {
        deletePropertyPath(runConfigData, path);
      }
      onSaveSession({runConfigYaml: yaml.stringify(runConfigData)});
    } catch (err) {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }
  };

  const runConfigSchema =
    configSchemaOrError?.__typename === 'RunConfigSchema' ? configSchemaOrError : undefined;
  const modeError =
    configSchemaOrError?.__typename === 'ModeNotFoundError' ? configSchemaOrError : undefined;

  const onScaffoldMissingConfig = () => {
    const config = runConfigSchema ? scaffoldPipelineConfig(runConfigSchema) : {};
    try {
      const runConfigData = yaml.parse(sanitizeConfigYamlString(currentSession.runConfigYaml));
      const updatedRunConfigData = merge(config, runConfigData);
      const runConfigYaml = yaml.stringify(updatedRunConfigData);
      onSaveSession({runConfigYaml});
    } catch (err) {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
    }
  };

  const buildExecutionVariables = () => {
    if (!currentSession) {
      return;
    }

    const configYamlOrEmpty = sanitizeConfigYamlString(currentSession.runConfigYaml);

    try {
      yaml.parse(configYamlOrEmpty);
    } catch (err) {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }

    return {
      executionParams: {
        runConfigData: configYamlOrEmpty,
        selector: {
          ...pipelineSelector,
          assetSelection: currentSession.assetSelection
            ? currentSession.assetSelection.map((a) => ({path: a.assetKey.path}))
            : undefined,
        },
        mode: currentSession.mode || 'default',
        executionMetadata: {
          tags: uniqBy(
            [
              // pass solid selection query via tags
              // clean up https://github.com/dagster-io/dagster/issues/2495
              ...(currentSession.solidSelectionQuery
                ? [
                    {
                      key: DagsterTag.SolidSelection,
                      value: currentSession.solidSelectionQuery,
                    },
                  ]
                : []),
              ...(currentSession?.base?.['presetName']
                ? [
                    {
                      key: DagsterTag.PresetName,
                      value: currentSession?.base?.['presetName'],
                    },
                  ]
                : []),

              ...(currentSession.assetSelection
                ? [
                    {
                      key: DagsterTag.StepSelection,
                      value: currentSession.assetSelection.flatMap((o) => o.opNames).join(','),
                    },
                  ]
                : []),

              ...tagsFromSession.map(onlyKeyAndValue),

              // note, we apply these last - uniqBy uses the first value it sees for
              // each key, so these can be overridden in the session
              ...pipeline.tags.map(onlyKeyAndValue),
            ],
            (tag) => tag.key,
          ),
        },
      },
    };
  };

  const saveTags = (tags: PipelineRunTag[]) => {
    const tagDict = {};
    const toSave: PipelineRunTag[] = [];
    tags.forEach((tag: PipelineRunTag) => {
      if (!(tag.key in tagDict)) {
        tagDict[tag.key] = tag.value;
        toSave.push(tag);
      }
    });
    onSaveSession({tags: toSave});
  };

  const checkConfig = async (configYaml: string) => {
    // Another request to preview a newer document may be made while this request
    // is in flight, in which case completion of this async method should not set loading=false.
    previewCounter.current += 1;
    const currentPreviewCount = previewCounter.current;
    const configYamlOrEmpty = sanitizeConfigYamlString(configYaml);

    dispatch({type: 'preview-loading', payload: true});

    const {data} = await client.query<PreviewConfigQuery, PreviewConfigQueryVariables>({
      fetchPolicy: 'no-cache',
      query: PREVIEW_CONFIG_QUERY,
      variables: {
        runConfigData: configYamlOrEmpty,
        pipeline: pipelineSelector,
        mode: currentSession.mode || 'default',
      },
    });

    if (mounted.current) {
      const isLatestRequest = currentPreviewCount === previewCounter.current;
      dispatch({
        type: 'set-preview',
        payload: {
          preview: data,
          previewedDocument: configYamlOrEmpty,
          previewLoading: isLatestRequest ? false : state.previewLoading,
        },
      });
    }

    return responseToYamlValidationResult(configYamlOrEmpty, data.isPipelineConfigValid);
  };

  const tagsApplyingNewBaseTags = (newBaseTags: PipelineRunTag[]) => {
    // If you choose a new base (preset or partition), we want to make a best-effort to preserve
    // the tags you've manually typed in, but remove:
    // - Tags that were in your previous base and are unchanged
    // - Tags that are specified in the new base
    const preservedUserTags = currentSession.base
      ? tagsFromSession.filter(
          (t) =>
            currentSession.base?.tags &&
            !currentSession.base?.tags.some((bt) => bt.key === t.key && bt.value === t.value) &&
            !newBaseTags.some((bt) => bt.key === t.key),
        )
      : [];

    return [...newBaseTags, ...preservedUserTags];
  };

  const onSelectPreset = async (preset: Preset) => {
    const newBaseTags = preset.tags.map(onlyKeyAndValue);

    onSaveSession({
      base: {presetName: preset.name, tags: newBaseTags},
      name: preset.name,
      runConfigYaml: preset.runConfigYaml || '',
      solidSelection: preset.solidSelection,
      solidSelectionQuery: preset.solidSelection === null ? '*' : preset.solidSelection.join(','),
      mode: preset.mode,
      tags: tagsApplyingNewBaseTags(newBaseTags),
      needsRefresh: false,
    });
  };

  const onSelectPartition = async (
    repositorySelector: RepositorySelector,
    partitionSetName: string,
    partitionName: string,
    sessionSolidSelection?: string[] | null,
  ) => {
    onConfigLoading();
    try {
      const {base} = currentSession;
      const {data} = await client.query<
        ConfigPartitionSelectionQuery,
        ConfigPartitionSelectionQueryVariables
      >({
        query: CONFIG_PARTITION_SELECTION_QUERY,
        variables: {repositorySelector, partitionSetName, partitionName},
      });

      if (
        !data ||
        !data.partitionSetOrError ||
        data.partitionSetOrError.__typename !== 'PartitionSet' ||
        !data.partitionSetOrError.partition
      ) {
        onConfigLoaded();
        return;
      }

      const {partition} = data.partitionSetOrError;

      let newBaseTags: {key: string; value: string}[] = [];
      if (partition.tagsOrError.__typename === 'PythonError') {
        showCustomAlert({
          body: <PythonErrorInfo error={partition.tagsOrError} />,
        });
      } else {
        newBaseTags = partition.tagsOrError.results.map(onlyKeyAndValue);
      }

      let runConfigYaml;
      if (partition.runConfigOrError.__typename === 'PythonError') {
        runConfigYaml = '';
        showCustomAlert({
          body: <PythonErrorInfo error={partition.runConfigOrError} />,
        });
      } else {
        runConfigYaml = partition.runConfigOrError.yaml;
      }

      const solidSelection = sessionSolidSelection || partition.solidSelection;

      onSaveSession({
        name: partition.name,
        base: Object.assign({}, base, {partitionName: partition.name, tags: newBaseTags}),
        runConfigYaml,
        solidSelection,
        solidSelectionQuery: solidSelection === null ? '*' : solidSelection.join(','),
        mode: partition.mode,
        tags: tagsApplyingNewBaseTags(newBaseTags),
        needsRefresh: false,
      });
    } catch {}
    onConfigLoaded();
  };

  const onRefreshConfig = async (base: SessionBase) => {
    // Handle preset-based configuration.
    if ('presetName' in base) {
      const {presetName} = base;
      const matchingPreset = pipeline.presets.find((preset) => preset.name === presetName);
      if (matchingPreset) {
        onSelectPreset({
          ...matchingPreset,
          solidSelection: currentSession.solidSelection || matchingPreset.solidSelection,
        });
      }
      return;
    }

    // Otherwise, handle partition-based configuration.
    const {partitionName, partitionsSetName} = base;
    const repositorySelector = repoAddressToSelector(repoAddress);

    // It is expected that `partitionName` is set here, since we shouldn't be showing the
    // button at all otherwise.
    if (partitionName) {
      onConfigLoading();
      await onSelectPartition(
        repositorySelector,
        partitionsSetName,
        partitionName,
        currentSession.solidSelection,
      );
      onConfigLoaded();
    }
  };

  const onDismissRefreshWarning = () => {
    onSaveSession({needsRefresh: false});
  };

  const openTagEditor = () => dispatch({type: 'toggle-tag-editor', payload: true});
  const closeTagEditor = () => dispatch({type: 'toggle-tag-editor', payload: false});

  const onConfigLoading = () => dispatch({type: 'toggle-config-loading', payload: true});
  const onConfigLoaded = () => dispatch({type: 'toggle-config-loading', payload: false});

  const {
    preview,
    previewLoading,
    previewedDocument,
    configLoading,
    editorHelpContext,
    tagEditorOpen,
  } = state;

  const refreshableSessionBase = React.useMemo(() => {
    const {base, needsRefresh} = currentSession;
    if (
      base &&
      needsRefresh &&
      ('presetName' in base || (base.partitionsSetName && base.partitionName))
    ) {
      return base;
    }
    return null;
  }, [currentSession]);

  let launchButtonTitle: string | undefined;
  if (launchpadType === 'asset') {
    launchButtonTitle = 'Materialize';
  }

  let launchButtonWarning: string | undefined;
  if (
    partitionSets.results.length &&
    currentSession.base &&
    'partitionsSetName' in currentSession.base &&
    !currentSession.base.partitionName
  ) {
    launchButtonWarning =
      'This job is partitioned. Are you sure you want to launch' +
      ' a run without a partition specified?';
  }

  return (
    <>
      <SplitPanelContainer
        axis="vertical"
        identifier="execution"
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
                onSaveSession={onSaveSession}
                onSelectPreset={onSelectPreset}
                onSelectPartition={onSelectPartition}
                repoAddress={repoAddress}
              />
              <SessionSettingsSpacer />
              {launchpadType === 'asset' ? (
                <TextInput
                  readOnly
                  value={
                    currentSession.assetSelection
                      ? currentSession.assetSelection
                          .map((a) => tokenForAssetKey(a.assetKey))
                          .join(', ')
                      : '*'
                  }
                />
              ) : (
                <OpSelector
                  serverProvidedSubsetError={
                    preview?.isPipelineConfigValid.__typename === 'InvalidSubsetError'
                      ? preview.isPipelineConfigValid
                      : undefined
                  }
                  pipelineName={pipeline.name}
                  value={currentSession.solidSelection || null}
                  query={currentSession.solidSelectionQuery || null}
                  onChange={onOpSelectionChange}
                  flattenGraphs={currentSession.flattenGraphs}
                  onFlattenGraphsChange={onFlattenGraphsChange}
                  repoAddress={repoAddress}
                />
              )}

              {isJob ? (
                <span />
              ) : (
                <>
                  <SessionSettingsSpacer />
                  <ConfigEditorModePicker
                    modes={pipeline.modes}
                    modeError={modeError}
                    onModeChange={onModeChange}
                    modeName={currentSession.mode}
                  />
                </>
              )}
              <TagEditor
                tagsFromDefinition={pipeline.tags}
                tagsFromSession={tagsFromSession}
                onChange={saveTags}
                open={tagEditorOpen}
                onRequestClose={closeTagEditor}
              />
              <div style={{flex: 1}} />
              <ShortcutHandler
                shortcutLabel="⌥T"
                shortcutFilter={(e) => e.code === 'KeyT' && e.altKey}
                onShortcut={openTagEditor}
              >
                <Button onClick={openTagEditor} icon={<Icon name="edit" />}>
                  Edit tags
                </Button>
              </ShortcutHandler>
              <SessionSettingsSpacer />
              <SecondPanelToggle axis="horizontal" container={editorSplitPanelContainer} />
            </SessionSettingsBar>
            {pipeline.tags.length || tagsFromSession.length ? (
              <Box
                padding={{vertical: 8, left: 12, right: 0}}
                border={{side: 'bottom', width: 1, color: Colors.Gray200}}
              >
                <TagContainer
                  tagsFromDefinition={pipeline.tags}
                  tagsFromSession={tagsFromSession}
                  onRequestEdit={openTagEditor}
                />
              </Box>
            ) : null}
            {refreshableSessionBase ? (
              <Box
                padding={{vertical: 8, horizontal: 12}}
                border={{side: 'bottom', width: 1, color: Colors.Gray200}}
              >
                <Group direction="row" spacing={8} alignItems="center">
                  <Icon name="warning" color={Colors.Yellow500} />
                  <div>
                    Your repository has been manually refreshed, and this configuration may now be
                    out of date.
                  </div>
                  <Button
                    intent="primary"
                    onClick={() => onRefreshConfig(refreshableSessionBase)}
                    disabled={state.configLoading}
                  >
                    Refresh config
                  </Button>
                  <Button onClick={onDismissRefreshWarning}>Dismiss</Button>
                </Group>
              </Box>
            ) : null}
            <SplitPanelContainer
              ref={editorSplitPanelContainer}
              axis="horizontal"
              identifier="execution-editor"
              firstMinSize={100}
              firstInitialPercent={70}
              first={
                <ConfigEditor
                  ref={editor}
                  readOnly={false}
                  configSchema={runConfigSchema}
                  configCode={currentSession.runConfigYaml}
                  onConfigChange={onConfigChange}
                  onHelpContextChange={(next) => {
                    if (!isHelpContextEqual(editorHelpContext, next)) {
                      dispatch({type: 'set-editor-help-context', payload: next});
                    }
                  }}
                  checkConfig={checkConfig}
                />
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
              isLoading={previewLoading}
              message={!runConfigSchema ? LOADING_CONFIG_SCHEMA : LOADING_RUN_PREVIEW}
            />
            <RunPreview
              launchpadType={launchpadType}
              document={previewedDocument}
              validation={preview ? preview.isPipelineConfigValid : null}
              solidSelection={currentSession.solidSelection}
              runConfigSchema={runConfigSchema}
              onHighlightPath={(path) => editor.current?.moveCursorToPath(path)}
              onRemoveExtraPaths={(paths) => onRemoveExtraPaths(paths)}
              onScaffoldMissingConfig={onScaffoldMissingConfig}
            />
          </>
        }
      />

      <LaunchButtonContainer launchpadType={launchpadType}>
        <LaunchRootExecutionButton
          title={launchButtonTitle}
          warning={launchButtonWarning}
          pipelineName={pipeline.name}
          getVariables={buildExecutionVariables}
          disabled={preview?.isPipelineConfigValid?.__typename !== 'PipelineConfigValidationValid'}
          behavior="open"
        />
      </LaunchButtonContainer>
    </>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default LaunchpadSession;

// This helper removes __typename, which prevents tags from being passed back to GraphQL
const onlyKeyAndValue = ({key, value}: {key: string; value: string}) => ({key, value});

const deletePropertyPath = (obj: any, path: string) => {
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
};

const sanitizeConfigYamlString = (yamlString: string) => (yamlString || '').trim() || '{}';

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
  ${RUN_PREVIEW_VALIDATION_FRAGMENT}
  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
`;

const SessionSettingsSpacer = styled.div`
  width: 5px;
`;

const RUN_CONFIG_SCHEMA_OR_ERROR_FRAGMENT = gql`
  fragment LaunchpadSessionRunConfigSchemaFragment on RunConfigSchemaOrError {
    __typename
    ... on RunConfigSchema {
      ...ConfigEditorRunConfigSchemaFragment
    }
    ... on ModeNotFoundError {
      message
    }
  }
  ${CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT}
`;

export const PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY = gql`
  query PipelineExecutionConfigSchemaQuery($selector: PipelineSelector!, $mode: String) {
    runConfigSchemaOrError(selector: $selector, mode: $mode) {
      ...LaunchpadSessionRunConfigSchemaFragment
    }
  }

  ${RUN_CONFIG_SCHEMA_OR_ERROR_FRAGMENT}
`;
