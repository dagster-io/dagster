import * as React from 'react';

import {
  applyChangesToSession,
  applyCreateSession,
  IExecutionSessionChanges,
  useExecutionSessionStorage,
  useInitialDataForMode,
} from '../app/ExecutionSessionStorage';
import {useFeatureFlags} from '../app/Flags';
import {useSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {RepoAddress} from '../workspace/types';

import LaunchpadSession from './LaunchpadSession';
import {LaunchpadTabs} from './LaunchpadTabs';
import {LaunchpadType} from './types';
import {
  LaunchpadSessionPartitionSetsFragment,
  LaunchpadSessionPipelineFragment,
} from './types/LaunchpadAllowedRoot.types';

interface Props {
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  rootDefaultYaml: string | undefined;
}

export const LaunchpadStoredSessionsContainer = (props: Props) => {
  const {launchpadType, pipeline, partitionSets, repoAddress, rootDefaultYaml} = props;

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
      />
    </>
  );
};

// eslint-disable-next-line import/no-default-export
export default LaunchpadStoredSessionsContainer;
