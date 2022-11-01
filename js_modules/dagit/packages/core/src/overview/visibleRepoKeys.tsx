import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';

export const visibleRepoKeys = (visibleRepos: DagsterRepoOption[]) => {
  return new Set(
    visibleRepos.map((option) =>
      repoAddressAsString(buildRepoAddress(option.repository.name, option.repositoryLocation.name)),
    ),
  );
};
