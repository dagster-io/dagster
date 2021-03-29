import {buildRepoAddress} from './buildRepoAddress';
import {RepoAddress} from './types';

export const repoAddressFromPath = (path: string): RepoAddress | null => {
  const postSplit = path.split('@');
  if (postSplit.length === 2) {
    const [name, location] = postSplit;
    return buildRepoAddress(name, location);
  }
  return null;
};
