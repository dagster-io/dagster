import {
  Body,
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  SplitPanelContainer,
  SplitPanelContainerHandle,
  TextInput,
} from '@dagster-io/ui-components';
import {
  ConfigEditorHandle,
  ConfigEditorHelp,
  ConfigEditorHelpContext,
  NewConfigEditor,
  isHelpContextEqual,
} from '@dagster-io/ui-components/editor';
import {LaunchRootExecutionButton} from '@shared/launchpad/LaunchRootExecutionButton';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';
import styled from 'styled-components';
import * as yaml from 'yaml';

import {ConfigEditorConfigPicker} from './ConfigEditorConfigPicker';
import {ConfigEditorModePicker} from './ConfigEditorModePicker';
import {fetchTagsAndConfigForAssetJob, fetchTagsAndConfigForJob} from './ConfigFetch';
import {LaunchpadConfigExpansionButton} from './LaunchpadConfigExpansionButton';
import {LoadingOverlay} from './LoadingOverlay';
import {OpSelector} from './OpSelector';
import {RUN_PREVIEW_VALIDATION_FRAGMENT, RunPreview} from './RunPreview';
import {SessionSettingsBar} from './SessionSettingsBar';
import {TagContainer, TagEditor} from './TagEditor';
import {scaffoldConfig} from './scaffoldType';
import {LaunchpadType} from './types';
import {
  LaunchpadSessionPartitionSetsFragment,
  LaunchpadSessionPipelineFragment,
} from './types/LaunchpadAllowedRoot.types';
import {PreviewConfigQuery, PreviewConfigQueryVariables} from './types/LaunchpadSession.types';
import {mergeYaml, sanitizeConfigYamlString} from './yamlUtils';
import {gql, useApolloClient} from '../apollo-client';
import {ConfigEditorPipelinePresetFragment} from './types/ConfigEditorConfigPicker.types';
import {usePartitionSetDetailsForLaunchpad} from './usePartitionSetDetailsForLaunchpad';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {
  IExecutionSession,
  IExecutionSessionChanges,
  PipelineRunTag,
  SessionBase,
} from '../app/ExecutionSessionStorage';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {useJobPermissions} from '../app/useJobPermissions';
import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {asAssetCheckHandleInput, asAssetKeyInput} from '../assets/asInput';
import {
  CONFIG_EDITOR_VALIDATION_FRAGMENT,
  responseToYamlValidationResult,
} from '../configeditor/ConfigEditorUtils';
import {ConfigEditorRunConfigSchemaFragment} from '../configeditor/types/ConfigEditorUtils.types';
import {
  AssetCheckCanExecuteIndividually,
  ExecutionParams,
  PipelineSelector,
  RepositorySelector,
} from '../graphql/types';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {DagsterTag} from '../runs/RunTag';
import {useCopyAction} from '../runs/RunTags';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

// Define the type for the config object passed to onSaveConfig
export interface LaunchpadConfig {
  runConfigYaml: string;
  mode: string | null;
  pipelineName: string;
  repoAddress: RepoAddress;
}

const YAML_SYNTAX_INVALID = `The YAML you provided couldn't be parsed. Please fix the syntax errors and try again.`;
const LOADING_CONFIG_FOR_PARTITION = `Generating configuration...`;
const LOADING_CONFIG_SCHEMA = `Loading config schema...`;
const LOADING_RUN_PREVIEW = `Checking config...`;

type Preset = ConfigEditorPipelinePresetFragment;

interface LaunchpadSessionProps {
  session: IExecutionSession;
  onSave: (changes: React.SetStateAction<IExecutionSessionChanges>) => void;
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  initialExecutionSessionState?: Partial<IExecutionSession>;
  runConfigSchema: ConfigEditorRunConfigSchemaFragment | undefined;
  rootDefaultYaml: string | undefined;
  onSaveConfig?: (config: LaunchpadConfig) => void;
}

interface ILaunchpadSessionState {
  preview: PreviewConfigQuery | null;
  previewDefaultsToExpand: boolean;
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
        previewDefaultsToExpand: boolean;
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
      const {preview, previewedDocument, previewDefaultsToExpand, previewLoading} = action.payload;
      return {
        ...state,
        preview,
        previewedDocument,
        previewDefaultsToExpand,
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

const LaunchButtonContainer = ({
  launchpadType,
  children,
}: {
  launchpadType: LaunchpadType;
  children: React.ReactNode;
}) => {
  if (launchpadType === 'asset') {
    return (
      <Box flex={{direction: 'row'}} border="top" padding={{right: 12, vertical: 8}}>
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
  previewDefaultsToExpand: false,
  previewedDocument: null,
  configLoading: false,
  editorHelpContext: null,
  tagEditorOpen: false,
};

const LaunchpadSession = (props: LaunchpadSessionProps) => {
  const {
    launchpadType,
    session: currentSession,
    onSave: onSaveSession,
    partitionSets,
    pipeline,
    repoAddress,
    rootDefaultYaml,
    onSaveConfig,
    runConfigSchema,
  } = props;

  const client = useApolloClient();
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const mounted = React.useRef<boolean>(false);
  const editor = React.useRef<ConfigEditorHandle | null>(null);
  const previewCounter = React.useRef(0);

  const {isJob} = pipeline;
  const tagsFromSession = React.useMemo(() => currentSession.tags || [], [currentSession]);

  const pipelineSelector: PipelineSelector = React.useMemo(() => {
    return {
      ...repoAddressToSelector(repoAddress),
      pipelineName: pipeline.name,
      solidSelection: currentSession.solidSelection || undefined,
      assetSelection: currentSession.assetSelection?.map(asAssetKeyInput) || [],
      assetCheckSelection: currentSession.assetChecksAvailable?.map(asAssetCheckHandleInput) || [],
    };
  }, [
    currentSession.solidSelection,
    currentSession.assetSelection,
    currentSession.assetChecksAvailable,
    pipeline.name,
    repoAddress,
  ]);

  const {hasLaunchExecutionPermission, loading} = useJobPermissions(
    pipelineSelector,
    repoAddress.location,
  );
  useBlockTraceUntilTrue('Permissions', !loading);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  });

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
    } catch {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }
  };

  const onScaffoldMissingConfig = () => {
    const config = runConfigSchema ? scaffoldConfig(runConfigSchema) : {};

    // Unmergeable scaffolded config. Don't do anything with this.
    if (!config || typeof config !== 'object') {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }

    try {
      onSaveSession({runConfigYaml: mergeYaml(config, currentSession.runConfigYaml)});
    } catch {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
    }
  };

  const onExpandDefaults = () => {
    if (rootDefaultYaml) {
      onSaveSession({runConfigYaml: mergeYaml(rootDefaultYaml, currentSession.runConfigYaml)});
    }
  };

  const [showChecks, setShowChecks] = React.useState<
    typeof currentSession.assetChecksAvailable | null
  >(null);
  const includedChecks =
    currentSession.assetChecksAvailable?.filter(
      (a) => a.canExecuteIndividually === AssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION,
    ) ?? [];

  const executableChecks =
    currentSession.assetChecksAvailable?.filter(
      (a) => a.canExecuteIndividually === AssetCheckCanExecuteIndividually.CAN_EXECUTE,
    ) ?? [];

  const buildExecutionVariables = () => {
    if (!currentSession) {
      return;
    }

    const configYamlOrEmpty = sanitizeConfigYamlString(currentSession.runConfigYaml);

    try {
      yaml.parse(configYamlOrEmpty);
    } catch {
      showCustomAlert({title: 'Invalid YAML', body: YAML_SYNTAX_INVALID});
      return;
    }

    const executionParams: ExecutionParams = {
      runConfigData: configYamlOrEmpty,
      selector: {
        ...pipelineSelector,
        assetSelection: currentSession.assetSelection
          ? currentSession.assetSelection.map(asAssetKeyInput)
          : [],
        assetCheckSelection: currentSession.includeSeparatelyExecutableChecks
          ? [...includedChecks, ...executableChecks].map(asAssetCheckHandleInput)
          : [...includedChecks].map(asAssetCheckHandleInput),
      },
      mode: currentSession.mode || 'default',
      executionMetadata: {
        tags: uniqBy(
          [
            // Include a dagster/solid_selection tag for non-asset jobs
            // (asset jobs indicate elsewhere in the UI which assets were selected)
            ...(currentSession.solidSelectionQuery && !pipeline.isAssetJob
              ? [
                  {
                    key: DagsterTag.SolidSelection,
                    value: currentSession.solidSelectionQuery,
                  },
                ]
              : []),
            ...(currentSession?.base && (currentSession?.base as any)['presetName']
              ? [
                  {
                    key: DagsterTag.PresetName,
                    value: (currentSession?.base as any)['presetName'],
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
    };
    return {executionParams};
  };

  const saveTags = (tags: PipelineRunTag[]) => {
    const tagDict = {};
    const toSave: PipelineRunTag[] = [];
    tags.forEach((tag: PipelineRunTag) => {
      if (!(tag.key in tagDict)) {
        (tagDict as any)[tag.key] = tag.value;
        toSave.push(tag);
      }
    });
    onSaveSession({tags: toSave});
  };

  const checkConfig = React.useCallback(
    async (configYaml: string) => {
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
          // for backfills (which have onSaveConfig set), asset checks are not explicitly
          // selected, so we pass in null to align with the backfill daemon implementation
          pipeline: props.onSaveConfig
            ? {
                ...pipelineSelector,
                assetCheckSelection: null,
              }
            : pipelineSelector,
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
            previewDefaultsToExpand: isLatestRequest
              ? hasDefaultsToExpand(rootDefaultYaml, configYamlOrEmpty)
              : state.previewDefaultsToExpand,
          },
        });
      }

      return responseToYamlValidationResult(configYamlOrEmpty, data.isPipelineConfigValid);
    },
    [
      client,
      currentSession.mode,
      pipelineSelector,
      rootDefaultYaml,
      state.previewLoading,
      state.previewDefaultsToExpand,
      props.onSaveConfig,
    ],
  );

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
      base: {type: 'preset', presetName: preset.name, tags: newBaseTags},
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

      const resp = props.session.assetSelection
        ? await fetchTagsAndConfigForAssetJob(client, {
            ...repositorySelector,
            jobName: pipeline.name,
            assetKeys: props.session.assetSelection.map(asAssetKeyInput),
            partitionName,
          })
        : await fetchTagsAndConfigForJob(client, {
            repositorySelector,
            partitionSetName,
            partitionName,
          });

      if (!resp) {
        onConfigLoaded();
        return;
      }

      const solidSelection = sessionSolidSelection || resp.solidSelection;

      onSaveSession({
        name: partitionName,
        base: Object.assign({}, base, {partitionName, tags: resp.tags}),
        runConfigYaml: mergeYaml(currentSession.runConfigYaml, resp.yaml),
        solidSelection,
        solidSelectionQuery: solidSelection === null ? '*' : solidSelection.join(','),
        mode: resp.mode,
        tags: tagsApplyingNewBaseTags(resp.tags),
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
    const repositorySelector = repoAddressToSelector(repoAddress);

    // It is expected that `partitionName` is set here, since we shouldn't be showing the
    // button at all otherwise.
    if (base.partitionName) {
      onConfigLoading();
      await onSelectPartition(
        repositorySelector,
        'partitionsSetName' in base ? base.partitionsSetName : '',
        base.partitionName,
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

  const splitPanelRef = React.useRef<SplitPanelContainerHandle>(null);

  const repositorySelector = React.useMemo(() => repoAddressToSelector(repoAddress), [repoAddress]);
  const partitionSetDetails = usePartitionSetDetailsForLaunchpad({
    pipelineName: pipeline.name,
    partitionSetName:
      currentSession.base && 'partitionsSetName' in currentSession.base
        ? currentSession.base.partitionsSetName
        : '',
    assetSelection: currentSession.assetSelection,
    repositorySelector,
    // do not fetch config for backfill launchpad because the core job
    // will often have multiple partitions defs, which will cause the
    // queries to fail
    skipConfigQuery: !!onSaveConfig,
  });
  const {
    preview,
    previewLoading,
    previewedDocument,
    previewDefaultsToExpand,
    configLoading,
    editorHelpContext,
    tagEditorOpen,
  } = state;

  const refreshableSessionBase = React.useMemo(() => {
    const {base, needsRefresh} = currentSession;
    if (
      base &&
      needsRefresh &&
      ('presetName' in base || ('partitionName' in base && base.partitionName))
    ) {
      return base;
    }
    return null;
  }, [currentSession]);

  const showRefreshWarning = !!(
    refreshableSessionBase ||
    (currentSession.needsRefresh && !currentSession.base)
  );

  let launchButtonTitle: string | undefined;
  if (launchpadType === 'asset') {
    launchButtonTitle = 'Materialize';
  }

  let launchButtonWarning: string | undefined;
  if (
    (partitionSets.results.length || partitionSetDetails.doesAnyAssetHavePartitions) &&
    isMissingPartition(currentSession.base)
  ) {
    launchButtonWarning =
      'This job is partitioned. Are you sure you want to launch' +
      ' a run without a partition specified?';
  }

  const copyAction = useCopyAction();

  const sessionSettingsItems = () => {
    if (onSaveConfig) {
      return <div style={{flex: 1}} />;
    } else {
      return (
        <>
          <ConfigEditorConfigPicker
            partitionSetDetails={partitionSetDetails}
            pipeline={pipeline}
            partitionSets={partitionSets.results}
            base={currentSession.base}
            onSaveSession={onSaveSession}
            onSelectPreset={onSelectPreset}
            onSelectPartition={onSelectPartition}
            repoAddress={repoAddress}
            assetSelection={currentSession.assetSelection}
          />
          <SessionSettingsSpacer />
          {launchpadType === 'asset' ? (
            <Box flex={{gap: 16, alignItems: 'center'}}>
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
              {includedChecks.length > 0 ? (
                <Body color={Colors.textDefault()}>
                  {`Including `}
                  <ButtonLink onClick={() => setShowChecks(includedChecks)}>
                    {`${includedChecks.length.toLocaleString()} ${
                      includedChecks.length > 1 ? 'checks' : 'check'
                    }`}
                  </ButtonLink>
                </Body>
              ) : undefined}
              {executableChecks.length > 0 ? (
                <Checkbox
                  label={
                    <span>
                      {`Include `}
                      <ButtonLink onClick={() => setShowChecks(executableChecks)}>
                        {`${executableChecks.length.toLocaleString()} separately executable ${
                          executableChecks.length > 1 ? 'checks' : 'check'
                        }`}
                      </ButtonLink>
                    </span>
                  }
                  checked={currentSession.includeSeparatelyExecutableChecks}
                  onChange={() =>
                    onSaveSession({
                      includeSeparatelyExecutableChecks:
                        !currentSession.includeSeparatelyExecutableChecks,
                    })
                  }
                />
              ) : undefined}
            </Box>
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

          {!isJob && (
            <>
              <SessionSettingsSpacer />
              <ConfigEditorModePicker
                modes={pipeline.modes}
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
        </>
      );
    }
  };

  const submitActionButton = () => {
    if (onSaveConfig) {
      return (
        <Button
          intent="primary"
          onClick={() => {
            onSaveConfig({
              runConfigYaml: currentSession.runConfigYaml,
              mode: currentSession.mode,
              pipelineName: pipeline.name,
              repoAddress,
            });
          }}
          disabled={preview?.isPipelineConfigValid?.__typename !== 'PipelineConfigValidationValid'}
        >
          Save config
        </Button>
      );
    } else {
      return (
        <LaunchRootExecutionButton
          title={launchButtonTitle}
          warning={launchButtonWarning}
          hasLaunchPermission={hasLaunchExecutionPermission}
          pipelineName={pipeline.name}
          getVariables={buildExecutionVariables}
          disabled={preview?.isPipelineConfigValid?.__typename !== 'PipelineConfigValidationValid'}
          behavior="open"
        />
      );
    }
  };

  return (
    <>
      <Dialog
        isOpen={!!showChecks}
        title={`Asset Checks (${showChecks?.length})`}
        onClose={() => setShowChecks(null)}
      >
        <div style={{height: '340px', overflow: 'hidden'}}>
          <VirtualizedItemListForDialog
            items={showChecks || []}
            renderItem={(check) => {
              return (
                <div key={`${check.name}-${tokenForAssetKey(check.assetKey)}`}>
                  {`${check.name} on ${displayNameForAssetKey(check.assetKey)}`}
                </div>
              );
            }}
          />
        </div>
        <DialogFooter topBorder>
          <Button onClick={() => setShowChecks(null)}>Close</Button>
        </DialogFooter>
      </Dialog>
      <SplitPanelContainer
        axis="vertical"
        identifier="execution"
        firstMinSize={100}
        firstInitialPercent={75}
        first={
          <>
            <LoadingOverlay isLoading={configLoading} message={LOADING_CONFIG_FOR_PARTITION} />
            <SessionSettingsBar>
              {sessionSettingsItems()}

              <SessionSettingsSpacer />
              <LaunchpadConfigExpansionButton
                axis="horizontal"
                firstInitialPercent={75}
                getSize={splitPanelRef.current?.getSize}
                changeSize={splitPanelRef.current?.changeSize}
              />
            </SessionSettingsBar>
            {pipeline.tags.length || tagsFromSession.length ? (
              <Box
                padding={{vertical: 8, left: 12, right: 0}}
                border={{side: 'bottom', color: Colors.borderDefault()}}
              >
                <TagContainer
                  tagsFromDefinition={pipeline.tags}
                  tagsFromSession={tagsFromSession}
                  onRequestEdit={openTagEditor}
                  actions={[copyAction]}
                />
              </Box>
            ) : null}
            {showRefreshWarning ? (
              <Box
                padding={{vertical: 8, horizontal: 12}}
                border={{side: 'bottom', color: Colors.borderDefault()}}
              >
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                  <Icon name="warning" color={Colors.accentYellow()} />
                  <div>
                    {repoAddressAsHumanString(repoAddress)} has been manually refreshed, and this
                    configuration may now be out of date.
                  </div>
                  <Button
                    intent="primary"
                    onClick={() => {
                      if (refreshableSessionBase) {
                        onRefreshConfig(refreshableSessionBase);
                      } else {
                        onSaveSession({runConfigYaml: rootDefaultYaml || '', needsRefresh: false});
                      }
                    }}
                    disabled={state.configLoading}
                  >
                    Refresh config
                  </Button>
                  <Button onClick={onDismissRefreshWarning}>Dismiss</Button>
                </Box>
              </Box>
            ) : null}
            <SplitPanelContainer
              ref={splitPanelRef}
              axis="horizontal"
              identifier="execution-editor"
              firstMinSize={100}
              firstInitialPercent={70}
              first={
                <NewConfigEditor
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
              onExpandDefaults={onExpandDefaults}
              anyDefaultsToExpand={previewDefaultsToExpand}
            />
          </>
        }
      />
      <LaunchButtonContainer launchpadType={launchpadType}>
        {submitActionButton()}
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    obj = obj[parts[i]!];
    if (typeof obj === 'undefined') {
      return;
    }
  }

  const lastKey = parts.pop();
  if (lastKey) {
    delete obj[lastKey];
  }
};

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

  ${CONFIG_EDITOR_VALIDATION_FRAGMENT}
  ${RUN_PREVIEW_VALIDATION_FRAGMENT}
`;

const SessionSettingsSpacer = styled.div`
  width: 5px;
`;

function isMissingPartition(base: SessionBase | null) {
  if (base?.type === 'op-job-partition-set' || base?.type === 'asset-job-partition') {
    return !base.partitionName;
  }
  return false;
}

function hasDefaultsToExpand(rootDefaultYaml: string | undefined, runConfigYaml: string) {
  if (!rootDefaultYaml) {
    return false;
  }
  // "If we ran the expansion, would the Yaml be any different?"
  try {
    return (
      mergeYaml(rootDefaultYaml, runConfigYaml, {sortMapEntries: true}) !==
      mergeYaml({}, runConfigYaml, {sortMapEntries: true})
    );
  } catch {
    return false;
  }
}
