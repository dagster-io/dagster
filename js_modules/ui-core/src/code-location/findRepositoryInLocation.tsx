import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../workspace/types';

// Given a `RepoAddress` and a location entry, try to find the matching repository to determine
// whether there are actual code object definitions available for this `RepoAddress`.
// It is possible that we have an errored `locationEntry` at a dunder `RepoAddress`, in which
// case there are no actual code objects available.
export const findRepositoryInLocation = (
  locationEntry: WorkspaceLocationNodeFragment | null,
  repoAddress: RepoAddress,
) => {
  if (
    locationEntry?.__typename !== 'WorkspaceLocationEntry' ||
    locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation'
  ) {
    return null;
  }

  const location = locationEntry.locationOrLoadError;
  const matchingLocation = location.repositories.find((repo) => repo.name === repoAddress.name);
  return matchingLocation || null;
};
