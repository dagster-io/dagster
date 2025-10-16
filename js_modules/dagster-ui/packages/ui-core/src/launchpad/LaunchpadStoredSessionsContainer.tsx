import LaunchpadSession from './LaunchpadSession';
import {LaunchpadTabs} from './LaunchpadTabs';
import {LaunchpadType} from './types';
import {
  LaunchpadSessionPartitionSetsFragment,
  LaunchpadSessionPipelineFragment,
} from './types/LaunchpadAllowedRoot.types';
import {
  IExecutionSessionChanges,
  applyChangesToSession,
  applyCreateSession,
  useExecutionSessionStorage,
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
  rootDefaultYaml: string | undefined;
  runConfigSchema: ConfigEditorRunConfigSchemaFragment | undefined;
}

export const LaunchpadStoredSessionsContainer = (props: Props) => {
  const {launchpadType, pipeline, partitionSets, repoAddress, rootDefaultYaml, runConfigSchema} =
    props;

  const {flagDisableAutoLoadDefaults} = useFeatureFlags();
  const initialDataForMode = useInitialDataForMode(
    pipeline,
    partitionSets,
    rootDefaultYaml,
    !flagDisableAutoLoadDefaults,
  );
  const [data, onSave] = useExecutionSessionStorage(repoAddress, pipeline.name, initialDataForMode);

  const onCreateSession = () => {
    onSave((data) => applyCreateSession(data, initialDataForMode));
  };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const currentSession = data.sessions[data.current]!;

  const onSaveSession = useSetStateUpdateCallback<IExecutionSessionChanges>(
    currentSession,
    (changes: IExecutionSessionChanges) => {
      onSave((data) => applyChangesToSession(data, data.current, changes));
    },
  );

  return (
    <>
      <LaunchpadTabs data={data} onCreate={onCreateSession} onSave={onSave} />
      <LaunchpadSession
        launchpadType={launchpadType}
        session={currentSession}
        onSave={onSaveSession}
        pipeline={pipeline}
        partitionSets={partitionSets}
        repoAddress={repoAddress}
        rootDefaultYaml={rootDefaultYaml}
        runConfigSchema={runConfigSchema}
      />
    </>
  );
};

// eslint-disable-next-line import/no-default-export
export default LaunchpadStoredSessionsContainer;
