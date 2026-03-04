import memoize from 'lodash/memoize';

import {RepoAddress} from './types';

export const DUNDER_REPO_NAME = '__repository__';

const memo = memoize(
  (repoAddress: RepoAddress) => repoAddress,
  (repoAddress: RepoAddress) => buildRepoPathForURL(repoAddress.name, repoAddress.location),
);

export const buildRepoAddress = (name: string, location: string) => memo({name, location});

export const buildRepoPathForHuman = (name: string, location: string) => {
  return name === DUNDER_REPO_NAME ? location : `${name}@${location}`;
};

export const buildRepoPathForURL = (name: string, location: string) => {
  const encodedLocation = encodeURIComponent(location);
  return name === DUNDER_REPO_NAME ? encodedLocation : `${name}@${encodedLocation}`;
};
