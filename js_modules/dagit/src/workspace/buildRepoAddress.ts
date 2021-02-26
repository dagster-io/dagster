import {memoize} from 'src/app/Util';
import {RepoAddress} from 'src/workspace/types';

const memo = memoize<RepoAddress, RepoAddress>(
  (repoAddress: RepoAddress) => repoAddress,
  (repoAddress: RepoAddress) => `${repoAddress.name}@${repoAddress.location}`,
);

export const buildRepoAddress = (name: string, location: string) => memo({name, location});
