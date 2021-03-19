import {memoize} from '../app/Util';

import {RepoAddress} from './types';

const memo = memoize<RepoAddress, RepoAddress>(
  (repoAddress: RepoAddress) => repoAddress,
  (repoAddress: RepoAddress) => `${repoAddress.name}@${repoAddress.location}`,
);

export const buildRepoAddress = (name: string, location: string) => memo({name, location});
