import * as React from 'react';

import {
  applyChangesToSession,
  applyCreateSession,
  IExecutionSessionChanges,
  useExecutionSessionStorage,
  useInitialDataForMode,
} from '../app/ExecutionSessionStorage';
import {useFeatureFlags} from '../app/Flags';
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

  const {flagAutoLoadDefaults} = useFeatureFlags();
  const initialDataForMode = useInitialDataForMode(
    pipeline,
    partitionSets,
    rootDefaultYaml,
    flagAutoLoadDefaults,
  );
  const [data, onSave] = useExecutionSessionStorage(repoAddress, pipeline.name, initialDataForMode);

  const onCreateSession = () => {
    onSave(applyCreateSession(data, initialDataForMode));
  };

  const onSaveSession = (changes: IExecutionSessionChanges) => {
    onSave(applyChangesToSession(data, data.current, changes));
  };

  const currentSession = data.sessions[data.current];

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
      />
    </>
  );
};

// eslint-disable-next-line import/no-default-export
export default LaunchpadStoredSessionsContainer;
