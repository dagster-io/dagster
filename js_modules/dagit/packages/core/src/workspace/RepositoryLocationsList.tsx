import {Button} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {Timestamp} from '../app/time/Timestamp';
import {ReloadRepositoryLocationButton} from '../nav/ReloadRepositoryLocationButton';
import {useRepositoryLocationReload} from '../nav/useRepositoryLocationReload';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {Table} from '../ui/Table';
import {TagWIP} from '../ui/TagWIP';
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
        <div style={{display: 'flex', alignItems: 'start'}}>
          <TagWIP minimal intent="danger">
            Failed
          </TagWIP>
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
        <Button
          onClick={() => tryReload()}
          loading={reloading}
          icon={<IconWIP name="refresh" />}
          text="Reload"
          small
          minimal
          style={{marginTop: '-4px'}}
        />
      )}
    </ReloadRepositoryLocationButton>
  );
};

export const RepositoryLocationsList = () => {
  const {locationEntries, loading} = React.useContext(WorkspaceContext);

  if (loading && !locationEntries.length) {
    return <div style={{color: ColorsWIP.Gray400}}>Loading…</div>;
  }

  if (!locationEntries.length) {
    return <NonIdealState icon="error" title="No repository locations!" />;
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
                        <span style={{color: ColorsWIP.Gray400}}>{metadata.value}</span>
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
