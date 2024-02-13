import memoize from 'lodash/memoize';

import {RepoAddress} from './types';
import {RepositorySelector} from '../graphql/types';

export const repoAddressToSelector = memoize((repoAddress: RepoAddress): RepositorySelector => {
  return {
    repositoryName: repoAddress.name,
    repositoryLocationName: repoAddress.location,
  };
});
