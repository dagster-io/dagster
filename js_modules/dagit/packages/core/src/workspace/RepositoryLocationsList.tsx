import {Button, Classes, Colors, Dialog, NonIdealState, Tag} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useRepositoryLocationReload} from '../nav/ReloadRepositoryLocationButton';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';

import {WorkspaceContext} from './WorkspaceContext';
import {RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries as LocationOrError} from './types/RootRepositoriesQuery';

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
          <th colSpan={2}>Status</th>
        </tr>
      </thead>
      <tbody>
        {locationEntries.map((location) => (
          <tr key={location.name}>
            <td style={{width: '30%'}}>{location.name}</td>
            <td style={{width: '20%'}}>
              <LocationStatus locationOrError={location} />
            </td>
            <td style={{width: '100%'}}>
              <ReloadButton location={location.name} />
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
