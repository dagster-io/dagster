import * as React from 'react';

import {
  createSingleSession,
  IExecutionSession,
  IExecutionSessionChanges,
} from '../app/ExecutionSessionStorage';
import {RepoAddress} from '../workspace/types';

import {LaunchpadType} from './LaunchpadRoot';
import LaunchpadSession from './LaunchpadSession';
import {LaunchpadSessionPartitionSetsFragment} from './types/LaunchpadSessionPartitionSetsFragment';
import {LaunchpadSessionPipelineFragment} from './types/LaunchpadSessionPipelineFragment';

interface Props {
  launchpadType: LaunchpadType;
  pipeline: LaunchpadSessionPipelineFragment;
  partitionSets: LaunchpadSessionPartitionSetsFragment;
  repoAddress: RepoAddress;
  sessionPresets: Partial<IExecutionSession>;
}

export const LaunchpadTransientSessionContainer = (props: Props) => {
  const {launchpadType, pipeline, partitionSets, repoAddress, sessionPresets} = props;

  const initialSessionComplete = createSingleSession(sessionPresets);
  const [session, setSession] = React.useState<IExecutionSession>(initialSessionComplete);

  const onSaveSession = (changes: IExecutionSessionChanges) => {
    const newSession = {...session, ...changes};
    setSession(newSession);
  };

  return (
    <LaunchpadSession
      launchpadType={launchpadType}
      session={session}
      onSave={onSaveSession}
      pipeline={pipeline}
      partitionSets={partitionSets}
      repoAddress={repoAddress}
    />
  );
};
