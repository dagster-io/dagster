import {Button, Classes, Colors, Dialog, NonIdealState, Tag} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {Timestamp} from '../app/time/Timestamp';
import {useRepositoryLocationReload} from '../nav/ReloadRepositoryLocationButton';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';
import {Caption} from '../ui/Text';

import {WorkspaceContext} from './WorkspaceContext';
import {RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries as LocationOrError} from './types/RootRepositoriesQuery';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

const LocationStatus: React.FC<{locationOrError: LocationOrError}> = (props) => {
  const {locationOrError} = props;
  const [showDialog, setShowDialog] = React.useState(false);

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
        <Dialog
          isOpen={showDialog}
          title="Repository location error"
          onClose={() => setShowDialog(false)}
          style={{width: '90%'}}
        >
          <div className={Classes.DIALOG_BODY}>
            <div style={{marginBottom: '12px'}}>
              Error loading <strong>{locationOrError.name}</strong>. Try reloading the repository
              location after resolving the issue.
            </div>
            <PythonErrorInfo error={locationOrError.locationOrLoadError} />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={() => setShowDialog(false)}>OK</Button>
            </div>
          </div>
        </Dialog>
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
  const {reloading, onClick} = useRepositoryLocationReload(location);
  const {canReloadRepositoryLocation} = usePermissions();

  if (!canReloadRepositoryLocation) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <ButtonLink color={Colors.GRAY3}>Reload</ButtonLink>
      </Tooltip>
    );
  }

  return (
    <ButtonLink onClick={onClick}>
      <Group direction="row" spacing={4} alignItems="center">
        Reload
        {reloading ? <Spinner purpose="body-text" /> : null}
      </Group>
    </ButtonLink>
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
              <LocationStatus locationOrError={location} />
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
