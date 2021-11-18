import React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {Timestamp} from '../app/time/Timestamp';
import {ReloadRepositoryLocationButton} from '../nav/ReloadRepositoryLocationButton';
import {useRepositoryLocationReload} from '../nav/useRepositoryLocationReload';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';
import {TagWIP} from '../ui/TagWIP';
import {Caption} from '../ui/Text';
import {Tooltip} from '../ui/Tooltip';

import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
import {RepositoryRemoteLocationLink} from './RepositoryRemoteLocationLink';
import {WorkspaceContext} from './WorkspaceContext';
import {RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries as LocationOrError} from './types/RootRepositoriesQuery';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

const LocationStatus: React.FC<{location: string; locationOrError: LocationOrError}> = (props) => {
  const {location, locationOrError} = props;
  const [showDialog, setShowDialog] = React.useState(false);
  const {reloading, tryReload} = useRepositoryLocationReload(location);

  if (locationOrError.loadStatus === 'LOADING') {
    if (locationOrError.locationOrLoadError) {
      return (
        <TagWIP minimal intent="primary">
          Updating...
        </TagWIP>
      );
    } else {
      return (
        <TagWIP minimal intent="primary">
          Loading...
        </TagWIP>
      );
    }
  }

  if (locationOrError.locationOrLoadError?.__typename === 'PythonError') {
    return (
      <>
        <Box flex={{alignItems: 'center', gap: 12}}>
          <TagWIP minimal intent="danger">
            Failed
          </TagWIP>
          <ButtonLink onClick={() => setShowDialog(true)}>
            <span style={{fontSize: '14px'}}>View error</span>
          </ButtonLink>
        </Box>
        <RepositoryLocationNonBlockingErrorDialog
          location={location}
          isOpen={showDialog}
          error={locationOrError.locationOrLoadError}
          reloading={reloading}
          onDismiss={() => setShowDialog(false)}
          onTryReload={() => tryReload()}
        />
      </>
    );
  }

  return (
    <TagWIP minimal intent="success">
      Loaded
    </TagWIP>
  );
};

const ReloadButton: React.FC<{
  location: string;
}> = (props) => {
  const {location} = props;
  const {canReloadRepositoryLocation} = usePermissions();

  if (!canReloadRepositoryLocation) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <ButtonLink color={ColorsWIP.Gray400}>Reload</ButtonLink>
      </Tooltip>
    );
  }

  return (
    <ReloadRepositoryLocationButton location={location}>
      {({reloading, tryReload}) => (
        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
          <ButtonLink onClick={() => tryReload()}>Reload</ButtonLink>
          {reloading ? <Spinner purpose="body-text" /> : null}
        </Box>
      )}
    </ReloadRepositoryLocationButton>
  );
};

export const RepositoryLocationsList = () => {
  const {locationEntries, loading} = React.useContext(WorkspaceContext);

  if (loading && !locationEntries.length) {
    return (
      <Box flex={{gap: 8, alignItems: 'center'}} padding={{horizontal: 24}}>
        <Spinner purpose="body-text" />
        <div>Loading...</div>
      </Box>
    );
  }

  if (!locationEntries.length) {
    return (
      <Box padding={{vertical: 32}}>
        <NonIdealState
          icon="folder"
          title="No repository locations"
          description="When you add a repository location to this workspace, it will appear here."
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th>Repository location</th>
          <th>Status</th>
          <th colSpan={2}>Updated</th>
        </tr>
      </thead>
      <tbody>
        {locationEntries.map((location) => (
          <tr key={location.name}>
            <td style={{maxWidth: '50%'}}>
              <Group direction="column" spacing={4}>
                <strong>{location.name}</strong>
                <div>
                  {location.displayMetadata.map((metadata, idx) => {
                    const name = metadata.key === 'url' ? 'source' : metadata.key;
                    const display =
                      metadata.key === 'url' ? (
                        <RepositoryRemoteLocationLink repositoryUrl={metadata.value} />
                      ) : (
                        metadata.value
                      );

                    return (
                      <div key={idx}>
                        <Caption style={{wordBreak: 'break-word'}}>
                          {`${name}: `}
                          <span style={{color: ColorsWIP.Gray400}}>{display}</span>
                        </Caption>
                      </div>
                    );
                  })}
                </div>
              </Group>
            </td>
            <td>
              <LocationStatus location={location.name} locationOrError={location} />
            </td>
            <td style={{whiteSpace: 'nowrap'}}>
              <Timestamp timestamp={{unix: location.updatedTimestamp}} timeFormat={TIME_FORMAT} />
            </td>
            <td style={{width: '180px'}}>
              <ReloadButton location={location.name} />
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
