import {memoize} from 'src/Util';
import {RepoAddress} from 'src/workspace/types';

export const repoAddressFromPath = memoize<string, RepoAddress | null>((path: string) => {
  const postSplit = path.split('@');
  if (postSplit.length === 2) {
    const [name, location] = postSplit;
    return {name, location};
  }
  return null;
});
