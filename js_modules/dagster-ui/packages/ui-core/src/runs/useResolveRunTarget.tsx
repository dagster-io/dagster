import React from 'react';

import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {useRepositoryForRunWithoutSnapshot} from '../workspace/useRepositoryForRun';

export function useResolveRunTarget(
  run: Pick<RunTableRunFragment, 'pipelineName' | 'repositoryOrigin' | 'pipelineSnapshotId'>,
): {
  isJob: boolean;
  repoAddressGuess: RepoAddress | null;
} {
  const {pipelineName} = run;
  const repo = useRepositoryForRunWithoutSnapshot(run);

  const isJob = React.useMemo(() => {
    if (repo) {
      const pipelinesAndJobs = repo.match.repository.pipelines;
      const match = pipelinesAndJobs.find((pipelineOrJob) => pipelineOrJob.name === pipelineName);
      return !!match?.isJob;
    }
    return false;
  }, [repo, pipelineName]);

  const repoAddressGuess = React.useMemo(() => {
    if (repo) {
      const {match} = repo;
      return buildRepoAddress(match.repository.name, match.repositoryLocation.name);
    }
    return null;
  }, [repo]);

  return {isJob, repoAddressGuess};
}
