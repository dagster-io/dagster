import {
    Button,
    Colors,
    SplitPanelContainer,
    SplitPanelContainerHandle
} from '@dagster-io/ui-components';
import {
    ConfigEditorHandle,
    ConfigEditorHelp,
    ConfigEditorHelpContext,
    NewConfigEditor
} from '@dagster-io/ui-components/editor';
import * as React from 'react';
import styled from 'styled-components';

import { ConfigEditorModePicker } from './ConfigEditorModePicker';
import { LaunchpadConfigExpansionButton } from './LaunchpadConfigExpansionButton';
import { LoadingOverlay } from './LoadingOverlay';
import { RUN_PREVIEW_VALIDATION_FRAGMENT, RunPreview } from './RunPreview';
import { SessionSettingsBar } from './SessionSettingsBar';
import { LaunchpadType } from './types';
import {
    LaunchpadSessionPartitionSetsFragment,
    LaunchpadSessionPipelineFragment,
} from './types/LaunchpadAllowedRoot.types';
import {
    PreviewConfigQuery,
    PreviewConfigQueryVariables,
} from './types/LaunchpadSession.types';
import { gql, useApolloClient, useQuery } from '../apollo-client';
import {
    IExecutionSession,
    IExecutionSessionChanges
} from '../app/ExecutionSessionStorage';
import { usePermissionsForLocation } from '../app/Permissions';
import {
    CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT,
    CONFIG_EDITOR_VALIDATION_FRAGMENT,
    responseToYamlValidationResult,
} from '../configeditor/ConfigEditorUtils';
import { PipelineSelector } from '../graphql/types';
import { RepoAddress } from '../workspace/types';

const LOADING_CONFIG_SCHEMA = `Loading config schema...`;
const LOADING_RUN_PREVIEW = `Checking config...`;

interface BackfillLaunchpadSessionProps {
  session: IExecutionSession;
  onSave: (changes: React.SetStateAction<IExecutionSessionChanges>) => void;
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  rootDefaultYaml: string | undefined;
  onSaveConfig: (config: any) => void;
}

export const BackfillLaunchpadSession = (props: BackfillLaunchpadSessionProps) => {
  const {
    session,
    onSave,
    launchpadType,
    pipeline,
    partitionSets,
    repoAddress,
    rootDefaultYaml,
    onSaveConfig,
  } = props;

  const client = useApolloClient();
  const {
    permissions: {canLaunchPipelineExecution},
  } = usePermissionsForLocation(repoAddress.location);

  const [editorHelpContext, setEditorHelpContext] = React.useState<ConfigEditorHelpContext | null>(
    null,
  );

  const editor = React.useRef<ConfigEditorHandle>(null);
  const splitPanelRef = React.useRef<SplitPanelContainerHandle>(null);

  const currentSession = session;
  const currentRunConfigYaml = currentSession.runConfigYaml;

  const pipelineSelector: PipelineSelector = {
    pipelineName: pipeline.name,
    repositoryName: repoAddress.name,
    repositoryLocationName: repoAddress.location,
  };

  const runConfigSchemaResult = useQuery<
    any,
    any
  >(PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY, {
    variables: {selector: pipelineSelector, mode: currentSession.mode},
  });

  const runConfigSchema = runConfigSchemaResult.data?.runConfigSchemaOrError;
  const configLoading = runConfigSchemaResult.loading;

  const preview = useQuery<PreviewConfigQuery, PreviewConfigQueryVariables>(
    PREVIEW_CONFIG_QUERY,
    {
      variables: {
        pipeline: pipelineSelector,
        runConfigData: {yaml: currentRunConfigYaml || ''},
        mode: currentSession.mode,
      },
      skip: !currentRunConfigYaml,
    },
  );

  const previewLoading = preview.loading;
  const validation = responseToYamlValidationResult(runConfigSchema, currentRunConfigYaml);

  const onConfigChange = (newYaml: string) => {
    onSave({runConfigYaml: newYaml});
  };

  const onScaffoldMissingConfig = () => {
    if (!runConfigSchema || runConfigSchema.__typename !== 'RunConfigSchema') {
      return;
    }
    // Implementation would go here - similar to LaunchpadSession
  };

  const onExpandDefaults = () => {
    if (!runConfigSchema || runConfigSchema.__typename !== 'RunConfigSchema') {
      return;
    }
    // Implementation would go here - similar to LaunchpadSession
  };

  const onRemoveExtraPaths = (paths: string[]) => {
    // Implementation would go here - similar to LaunchpadSession
  };

  const anyDefaultsToExpand = false; // This would be calculated based on schema

  const handleSaveConfig = async () => {
    const config = {
      runConfigYaml: currentRunConfigYaml,
      mode: currentSession.mode,
      pipelineName: pipeline.name,
      repoAddress,
    };
    onSaveConfig(config);
  };

  const displayedDocument = currentRunConfigYaml || rootDefaultYaml || '';

  return (
    <>
      <SessionSettingsBar>
        <ConfigEditorModePicker
          modes={pipeline.modes}
          modeError={null}
          onModeChange={(mode) => onSave({mode})}
          modeName={currentSession.mode}
        />
        <div style={{flex: 1}} />
        <LaunchpadConfigExpansionButton
          axis="horizontal"
          firstInitialPercent={75}
          getSize={splitPanelRef.current?.getSize}
          changeSize={splitPanelRef.current?.changeSize}
        />
      </SessionSettingsBar>

      <SplitPanelContainer
        ref={splitPanelRef}
        axis="horizontal"
        first={
          <>
            <LoadingOverlay
              isLoading={configLoading}
              message={LOADING_CONFIG_SCHEMA}
            />
            <NewConfigEditor
              ref={editor}
              readOnly={false}
              value={displayedDocument}
              onChange={onConfigChange}
              onHelpContextChange={setEditorHelpContext}
              configSchema={runConfigSchema}
              checkConfig={async (config) => {
                const result = await preview.refetch({
                  variables: {
                    pipeline: pipelineSelector,
                    runConfigData: {yaml: config},
                    mode: currentSession.mode,
                  },
                });
                return result.data?.isPipelineConfigValid;
              }}
              onScaffoldMissingConfig={onScaffoldMissingConfig}
              onExpandDefaults={onExpandDefaults}
              onRemoveExtraPaths={onRemoveExtraPaths}
              anyDefaultsToExpand={anyDefaultsToExpand}
            />
            {editorHelpContext && (
              <ConfigEditorHelp
                context={editorHelpContext}
                allInnerTypes={runConfigSchema?.allConfigTypes || []}
              />
            )}
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
              document={displayedDocument}
              validation={preview ? preview.data?.isPipelineConfigValid : null}
              solidSelection={currentSession.solidSelection}
              runConfigSchema={runConfigSchema}
              onHighlightPath={(path) => editor.current?.moveCursorToPath(path)}
              onRemoveExtraPaths={onRemoveExtraPaths}
              onScaffoldMissingConfig={onScaffoldMissingConfig}
              onExpandDefaults={onExpandDefaults}
              anyDefaultsToExpand={anyDefaultsToExpand}
            />
          </>
        }
      />

      <LaunchButtonContainer launchpadType={launchpadType}>
        <Button
          intent="primary"
          onClick={handleSaveConfig}
          disabled={preview?.data?.isPipelineConfigValid?.__typename !== 'PipelineConfigValidationValid'}
        >
          Save Config
        </Button>
      </LaunchButtonContainer>
    </>
  );
};

const LaunchButtonContainer = styled.div<{launchpadType: LaunchpadType}>`
  padding: 12px 24px;
  border-top: 1px solid ${Colors.borderDefault()};
  background: ${Colors.backgroundDefault()};
  display: flex;
  justify-content: flex-end;
`;

const PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY = gql`
  query PipelineExecutionConfigSchemaQuery($selector: PipelineSelector!, $mode: String) {
    runConfigSchemaOrError(selector: $selector, mode: $mode) {
      ...LaunchpadSessionRunConfigSchemaFragment
    }
  }

  fragment LaunchpadSessionRunConfigSchemaFragment on RunConfigSchemaOrError {
    ... on RunConfigSchema {
      ...ConfigEditorRunConfigSchemaFragment
    }
    ... on ModeNotFoundError {
      ...LaunchpadSessionModeNotFound
    }
  }

  fragment LaunchpadSessionModeNotFound on ModeNotFoundError {
    message
  }

  ${CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT}
`;

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