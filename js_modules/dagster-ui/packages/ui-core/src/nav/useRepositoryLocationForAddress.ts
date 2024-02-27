import {useContext} from 'react';

import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export function useRepositoryLocationForAddress(repoAddress: RepoAddress) {
  const {locationEntries} = useContext(WorkspaceContext);
  return locationEntries.find(
    (r) =>
      r.locationOrLoadError?.__typename === 'RepositoryLocation' &&
      r.locationOrLoadError.repositories.some(
        (repo) => repo.name === repoAddress.name && repo.location.name === repoAddress.location,
      ),
  );
}
