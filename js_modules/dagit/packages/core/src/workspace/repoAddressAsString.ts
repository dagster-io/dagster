import {memoize} from '../app/Util';

import {buildRepoPath} from './buildRepoAddress';
import {RepoAddress} from './types';

export const repoAddressAsString = memoize<RepoAddress, string>((repoAddress: RepoAddress) =>
  buildRepoPath(repoAddress.name, repoAddress.location),
);
