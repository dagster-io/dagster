import {memoize} from 'src/app/Util';
import {RepositorySelector} from 'src/types/globalTypes';
import {RepoAddress} from 'src/workspace/types';

export const repoAddressToSelector = memoize<RepoAddress, RepositorySelector>(
  (repoAddress: RepoAddress): RepositorySelector => {
    return {
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    };
  },
);
