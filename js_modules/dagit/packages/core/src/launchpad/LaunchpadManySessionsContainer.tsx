import * as React from 'react';

import {
  applyChangesToSession,
  applyCreateSession,
  IExecutionSessionChanges,
  useExecutionSessionStorage,
  useInitialDataForMode,
} from '../app/ExecutionSessionStorage';
import {RepoAddress} from '../workspace/types';

import LaunchpadSessionContainer from './LaunchpadSessionContainer';
import {LaunchpadTabs} from './LaunchpadTabs';
import {LaunchpadSessionContainerPartitionSetsFragment} from './types/LaunchpadSessionContainerPartitionSetsFragment';
import {LaunchpadSessionContainerPipelineFragment} from './types/LaunchpadSessionContainerPipelineFragment';

interface Props {
  pipeline: LaunchpadSessionContainerPipelineFragment;
  partitionSets: LaunchpadSessionContainerPartitionSetsFragment;
  repoAddress: RepoAddress;
}

export const LaunchpadManySessionsContainer = (props: Props) => {
  const {pipeline, partitionSets, repoAddress} = props;

  const initialDataForMode = useInitialDataForMode(pipeline, partitionSets);
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
      <LaunchpadSessionContainer
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
export default LaunchpadManySessionsContainer;
