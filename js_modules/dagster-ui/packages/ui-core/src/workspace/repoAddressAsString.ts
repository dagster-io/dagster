import {buildRepoPathForHuman, buildRepoPathForURL} from './buildRepoAddress';
import {RepoAddress} from './types';

// Note: These are not memoized because the result is a primitive value and
// there are scenarios where the repoAddress argument is a temporary object,
// so WeakMapping the input to the output can cause the WeakMap to become
// huge before it's garbage collected. We could use memoize() with a cache-key
// function, but the cache-key generator would essentially BE this method,
// which would eat up any perf gains yielded by memoizing it.
//
export const repoAddressAsHumanString = (repoAddress: RepoAddress) => {
  return buildRepoPathForHuman(repoAddress.name, repoAddress.location);
};

export const repoAddressAsURLString = (repoAddress: RepoAddress) => {
  return buildRepoPathForURL(repoAddress.name, repoAddress.location);
};

// Unencoded, dunder repo visible.
export const repoAddressAsTag = (repoAddress: RepoAddress) => {
  return `${repoAddress.name}@${repoAddress.location}`;
};
