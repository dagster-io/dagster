import {Box, Button, Icon, NonIdealState} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
import {WorkspaceLocationNodeFragment} from './WorkspaceContext/types/WorkspaceQueries.types';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';

interface Props {
  repoAddress: RepoAddress;
  locationEntry: WorkspaceLocationNodeFragment | null;
}

export const CodeLocationNotFound = ({repoAddress, locationEntry}: Props) => {
  const displayName = repoAddressAsHumanString(repoAddress);
  const locationName = repoAddress.location;

  const [showDialog, setShowDialog] = useState(false);

  const reloadFn = useMemo(() => buildReloadFnForLocation(locationName), [locationName]);
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  if (locationEntry?.locationOrLoadError?.__typename === 'PythonError') {
    return (
      <>
        <NonIdealState
          icon="error_outline"
          title="Error loading code location"
          description={
            <Box flex={{direction: 'column', gap: 12}} style={{wordBreak: 'break-word'}}>
              <div>
                Code location <strong>{displayName}</strong> failed to load due to errors.
              </div>
              <div>
                <Button icon={<Icon name="error_outline" />} onClick={() => setShowDialog(true)}>
                  View errors
                </Button>
              </div>
            </Box>
          }
        />
        <RepositoryLocationNonBlockingErrorDialog
          location={locationName}
          isOpen={showDialog}
          error={locationEntry.locationOrLoadError}
          reloading={reloading}
          onDismiss={() => setShowDialog(false)}
          onTryReload={() => tryReload()}
        />
      </>
    );
  }

  return (
    <NonIdealState
      icon="code_location"
      title="Code location not found"
      description={
        <Box flex={{direction: 'column', gap: 12}} style={{wordBreak: 'break-word'}}>
          <div>
            Code location <strong>{displayName}</strong> is not available in this workspace.
          </div>
          <div>
            Check your <Link to="/deployment">deployment settings</Link> for errors.
          </div>
        </Box>
      }
    />
  );
};
