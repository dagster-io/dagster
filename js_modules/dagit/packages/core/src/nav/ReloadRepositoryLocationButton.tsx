import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {useFeatureFlags} from '../app/Flags';
import {RepositoryLocationErrorDialog} from '../workspace/RepositoryLocationErrorDialog';

import {buildReloadFnForLocation, useRepositoryLocationReload} from './useRepositoryLocationReload';

type ChildProps = {
  tryReload: () => void;
  reloading: boolean;
};

interface Props {
  children: (childProps: ChildProps) => React.ReactNode;
  location: string;
}

export const ReloadRepositoryLocationButton: React.FC<Props> = (props) => {
  const {children, location} = props;
  const [shown, setShown] = React.useState(false);

  const {basePath} = React.useContext(AppContext);
  const {flagNewWorkspace} = useFeatureFlags();

  const reloadFn = React.useMemo(() => buildReloadFnForLocation(location), [location]);
  const {reloading, error, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  React.useEffect(() => setShown(!!error), [error]);

  return (
    <>
      {children({tryReload, reloading})}
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
          window.location.href = flagNewWorkspace
            ? `${basePath}/instance/code-locations`
            : `${basePath}/workspace`;
        }}
      />
    </>
  );
};
