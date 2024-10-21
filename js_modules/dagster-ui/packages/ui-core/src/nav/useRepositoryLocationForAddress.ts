import {useContext} from 'react';

import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export function useRepositoryLocationForAddress(repoAddress: RepoAddress | null) {
  const {locationEntries} = useContext(WorkspaceContext);
  return repoAddress
    ? locationEntries.find(
        (r) =>
          r.locationOrLoadError?.__typename === 'RepositoryLocation' &&
          r.locationOrLoadError.repositories.some(
            (repo) => repo.name === repoAddress.name && repo.location.name === repoAddress.location,
          ),
      )
    : undefined;
}
