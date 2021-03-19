import {memoize} from '../app/Util';

import {RepoAddress} from './types';

export const repoAddressAsString = memoize<RepoAddress, string>((repoAddress: RepoAddress) => {
  return `${repoAddress.name}@${repoAddress.location}`;
});
