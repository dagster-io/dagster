import {Colors, NonIdealState, Tag} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {Timestamp} from '../app/time/Timestamp';
import {ReloadRepositoryLocationButton} from '../nav/ReloadRepositoryLocationButton';
import {useRepositoryLocationReload} from '../nav/useRepositoryLocationReload';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';
import {Caption} from '../ui/Text';

import {RepositoryLocationNonBlockingErrorDialog} from './RepositoryLocationErrorDialog';
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
        <Tag minimal intent="primary">
          Updating...
        </Tag>
      );
    } else {
      return (
        <Tag minimal intent="primary">
          Loading...
        </Tag>
      );
    }
  }

  if (locationOrError.locationOrLoadError?.__typename === 'PythonError') {
    return (
      <>
        <div style={{display: 'flex', alignItems: 'start'}}>
          <Tag minimal intent="danger">
            Failed
          </Tag>
          <div style={{fontSize: '14px', marginLeft: '8px'}}>
            <ButtonLink onClick={() => setShowDialog(true)}>View error</ButtonLink>
          </div>
        </div>
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
    <Tag minimal intent="success">
      Loaded
    </Tag>
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
        <ButtonLink color={Colors.GRAY3}>Reload</ButtonLink>
      </Tooltip>
    );
  }

  return (
    <ReloadRepositoryLocationButton location={location}>
      {({reloading, tryReload}) => (
        <ButtonLink onClick={() => tryReload()}>
          <Group direction="row" spacing={4} alignItems="center">
            Reload
            {reloading ? <Spinner purpose="body-text" /> : null}
          </Group>
        </ButtonLink>
      )}
    </ReloadRepositoryLocationButton>
  );
};

export const RepositoryLocationsList = () => {
  const {locationEntries, loading} = React.useContext(WorkspaceContext);

  if (loading && !locationEntries.length) {
    return <div style={{color: Colors.GRAY3}}>Loading…</div>;
  }

  if (!locationEntries.length) {
    return <NonIdealState icon="cube" title="No repository locations!" />;
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
                  {location.displayMetadata.map((metadata, idx) => (
                    <div key={idx}>
                      <Caption style={{wordBreak: 'break-word'}}>
                        {`${metadata.key}: `}
                        <span style={{color: Colors.GRAY3}}>{metadata.value}</span>
                      </Caption>
                    </div>
                  ))}
                </div>
              </Group>
            </td>
            <td>
              <LocationStatus location={location.name} locationOrError={location} />
            </td>
            <td style={{whiteSpace: 'nowrap'}}>
              <Timestamp timestamp={{unix: location.updatedTimestamp}} timeFormat={TIME_FORMAT} />
            </td>
            <td>
              <ReloadButton location={location.name} />
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
