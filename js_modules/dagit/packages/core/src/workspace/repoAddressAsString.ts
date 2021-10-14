import memoize from 'lodash/memoize';

import {buildRepoPath} from './buildRepoAddress';
import {RepoAddress} from './types';

export const repoAddressAsString = memoize((repoAddress: RepoAddress) =>
  buildRepoPath(repoAddress.name, repoAddress.location),
);
