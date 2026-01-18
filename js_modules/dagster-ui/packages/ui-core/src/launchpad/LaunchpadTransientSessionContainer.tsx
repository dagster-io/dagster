import {useState} from 'react';

import LaunchpadSession, {LaunchpadConfig} from './LaunchpadSession';
import {LaunchpadType} from './types';
import {
  LaunchpadSessionPartitionSetsFragment,
  LaunchpadSessionPipelineFragment,
} from './types/LaunchpadAllowedRoot.types';
import {
  IExecutionSession,
  IExecutionSessionChanges,
  createSingleSession,
  useInitialDataForMode,
} from '../app/ExecutionSessionStorage';
import {useFeatureFlags} from '../app/useFeatureFlags';
import {ConfigEditorRunConfigSchemaFragment} from '../configeditor/types/ConfigEditorUtils.types';
import {useSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {RepoAddress} from '../workspace/types';

interface Props {
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  sessionPresets: Partial<IExecutionSession>;
  rootDefaultYaml: string | undefined;
  onSaveConfig?: (config: LaunchpadConfig) => void;
  runConfigSchema: ConfigEditorRunConfigSchemaFragment | undefined;
}

export const LaunchpadTransientSessionContainer = (props: Props) => {
  const {
    launchpadType,
    pipeline,
    partitionSets,
    repoAddress,
    sessionPresets,
    rootDefaultYaml,
    onSaveConfig,
    runConfigSchema,
  } = props;

  const {flagDisableAutoLoadDefaults} = useFeatureFlags();
  const initialData = useInitialDataForMode(
    pipeline,
    partitionSets,
    rootDefaultYaml,
    !flagDisableAutoLoadDefaults,
  );

  // Avoid supplying an undefined `runConfigYaml` to the session.
  const initialSessionComplete = createSingleSession({
    ...sessionPresets,
    ...(initialData.runConfigYaml ? {runConfigYaml: initialData.runConfigYaml} : {}),
  });

  const [session, setSession] = useState<IExecutionSession>(initialSessionComplete);

  const onSaveSession = useSetStateUpdateCallback<IExecutionSessionChanges>(
    session,
    (changes: IExecutionSessionChanges) => {
      setSession((session) => ({...session, ...changes}));
    },
  );

  return (
    <LaunchpadSession
      launchpadType={launchpadType}
      session={session}
      onSave={onSaveSession}
      pipeline={pipeline}
      partitionSets={partitionSets}
      repoAddress={repoAddress}
      rootDefaultYaml={rootDefaultYaml}
      onSaveConfig={onSaveConfig}
      runConfigSchema={runConfigSchema}
    />
  );
};
