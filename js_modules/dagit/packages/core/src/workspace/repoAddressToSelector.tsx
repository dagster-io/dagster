import memoize from 'lodash/memoize';

import {RepositorySelector} from '../graphql/graphql';

import {RepoAddress} from './types';

export const repoAddressToSelector = memoize(
  (repoAddress: RepoAddress): RepositorySelector => {
    return {
      repositoryName: repoAddress.name,
      repositoryLocationName: repoAddress.location,
    };
  },
);
