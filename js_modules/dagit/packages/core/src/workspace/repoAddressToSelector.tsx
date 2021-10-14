import memoize from 'lodash/memoize';

import {RepositorySelector} from '../types/globalTypes';

import {RepoAddress} from './types';

export const repoAddressToSelector = memoize(
  (repoAddress: RepoAddress): RepositorySelector => {
    return {
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    };
  },
);
