import {memoize} from '../app/Util';
import {RepositorySelector} from '../types/globalTypes';

import {RepoAddress} from './types';

export const repoAddressToSelector = memoize<RepoAddress, RepositorySelector>(
  (repoAddress: RepoAddress): RepositorySelector => {
    return {
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    };
  },
);
