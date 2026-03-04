import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';

export const visibleRepoKeys = (visibleRepos: DagsterRepoOption[]) => {
  return new Set(
    visibleRepos.map((option) =>
      repoAddressAsHumanString(
        buildRepoAddress(option.repository.name, option.repositoryLocation.name),
      ),
    ),
  );
};
