import {useMemo} from 'react';

import {RunPageFragment} from './types/RunFragments.types';
import {isThisThingAJob} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';

export const useRunRepoInfo = (run: RunPageFragment | null | undefined) => {
  const repoMatch = useRepositoryForRunWithParentSnapshot(run);
  const repoAddress = repoMatch?.match
    ? buildRepoAddress(repoMatch.match.repository.name, repoMatch.match.repositoryLocation.name)
    : null;

  const isJob = useMemo(
    () => !!(run && repoMatch && isThisThingAJob(repoMatch.match, run.pipelineName)),
    [run, repoMatch],
  );

  return {repoAddress, isJob};
};
