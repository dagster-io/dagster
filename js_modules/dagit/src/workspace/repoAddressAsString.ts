import {memoize} from 'src/Util';
import {RepoAddress} from 'src/workspace/types';

export const repoAddressAsString = memoize<RepoAddress, string>((repoAddress: RepoAddress) => {
  return `${repoAddress.name}@${repoAddress.location}`;
});
