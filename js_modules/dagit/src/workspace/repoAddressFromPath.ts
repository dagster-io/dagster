import {buildRepoAddress} from 'src/workspace/buildRepoAddress';
import {RepoAddress} from 'src/workspace/types';

export const repoAddressFromPath = (path: string): RepoAddress | null => {
  const postSplit = path.split('@');
  if (postSplit.length === 2) {
    const [name, location] = postSplit;
    return buildRepoAddress(name, location);
  }
  return null;
};
