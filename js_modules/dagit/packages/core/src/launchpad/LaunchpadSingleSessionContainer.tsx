import * as React from 'react';

import {
  createSingleSession,
  IExecutionSessionChanges,
  useInitialDataForMode,
} from '../app/ExecutionSessionStorage';
import {RepoAddress} from '../workspace/types';

import LaunchpadSessionContainer from './LaunchpadSessionContainer';
import {LaunchpadSessionContainerPartitionSetsFragment} from './types/LaunchpadSessionContainerPartitionSetsFragment';
import {LaunchpadSessionContainerPipelineFragment} from './types/LaunchpadSessionContainerPipelineFragment';

interface Props {
  pipeline: LaunchpadSessionContainerPipelineFragment;
  partitionSets: LaunchpadSessionContainerPartitionSetsFragment;
  repoAddress: RepoAddress;
}

export const LaunchpadSingleSessionContainer = (props: Props) => {
  const {pipeline, partitionSets, repoAddress} = props;

  const initialDataForMode = useInitialDataForMode(pipeline, partitionSets);

  const [session, saveSession] = React.useState(() => createSingleSession(initialDataForMode));
  const onSaveSession = React.useCallback((changes: IExecutionSessionChanges) => {
    saveSession((current) => ({...current, ...changes}));
  }, []);

  return (
    <LaunchpadSessionContainer
      session={session}
      onSave={onSaveSession}
      pipeline={pipeline}
      partitionSets={partitionSets}
      repoAddress={repoAddress}
    />
  );
};
