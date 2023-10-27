import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {usePermissionsForLocation} from '../app/Permissions';
import {RepositoryLocationErrorDialog} from '../workspace/RepositoryLocationErrorDialog';

import {buildReloadFnForLocation, useRepositoryLocationReload} from './useRepositoryLocationReload';

export type ChildProps = {
  codeLocation: string;
  tryReload: () => void;
  reloading: boolean;
  hasReloadPermission: boolean;
};

interface Props {
  ChildComponent: React.FC<ChildProps>;
  location: string;
}

export const NO_RELOAD_PERMISSION_TEXT = 'You do not have permission to reload this code location';

export const ReloadRepositoryLocationButton: React.FC<Props> = (props) => {
  const {ChildComponent, location} = props;
  const [shown, setShown] = React.useState(false);

  const {basePath} = React.useContext(AppContext);

  const {
    permissions: {canReloadRepositoryLocation: hasReloadPermission},
  } = usePermissionsForLocation(location);

  const reloadFn = React.useMemo(() => buildReloadFnForLocation(location), [location]);
  const {reloading, error, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  React.useEffect(() => setShown(!!error), [error]);

  return (
    <>
      <ChildComponent {...{tryReload, reloading, hasReloadPermission, codeLocation: location}} />
      <RepositoryLocationErrorDialog
        location={location}
        isOpen={shown}
        error={error}
        reloading={reloading}
        onTryReload={tryReload}
        onDismiss={() => {
          // On dismiss, redirect to the Workspace view so that the location error
          // is presented to the user, and so that if the user was previously viewing
          // an object in a failed repo location, they aren't staring at a blank page.
          setShown(false);
          window.location.href = `${basePath}/locations`;
        }}
      />
    </>
  );
};
