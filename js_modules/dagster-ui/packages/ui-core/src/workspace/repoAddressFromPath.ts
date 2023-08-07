import {buildRepoAddress, DUNDER_REPO_NAME} from './buildRepoAddress';
import {RepoAddress} from './types';

export const repoAddressFromPath = (path: string): RepoAddress | null => {
  // Split on `@`. If there are any elements beyond the first two, we're going to ignore
  // them because they shouldn't be there -- the location name should be URI-encoded.
  const [beforeAt, afterAt] = path.split('@');

  // This is an empty string with no value to us here.
  if (!beforeAt) {
    return null;
  }

  // If there are no elements after `@`, this is a code location with a dunder repo name.
  if (!afterAt) {
    return buildRepoAddress(DUNDER_REPO_NAME, decodeURIComponent(beforeAt));
  }

  // It should not be necessary to decode repo name since we restrict repo names to characters
  // that do not need encoding.
  const repoName = beforeAt;
  const locationName = decodeURIComponent(afterAt);

  return buildRepoAddress(repoName, locationName);
};
