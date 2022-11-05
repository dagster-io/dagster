import * as React from 'react';

import {useCodeLocationsStatus} from '../nav/useCodeLocationsStatus';

import {StatusAndMessage} from './DeploymentStatusType';
import {useDaemonStatus} from './useDaemonStatus';

export type DeploymentStatusType = 'code-locations' | 'daemons';

type DeploymentStatus = {
  codeLocations: StatusAndMessage | null;
  daemons: StatusAndMessage | null;
};

export const DeploymentStatusContext = React.createContext<DeploymentStatus>({
  codeLocations: null,
  daemons: null,
});

interface Props {
  include: Set<DeploymentStatusType>;
}

export const DeploymentStatusProvider: React.FC<Props> = (props) => {
  const {children, include} = props;

  const codeLocations = useCodeLocationsStatus(!include.has('code-locations'));
  const daemons = useDaemonStatus(!include.has('daemons'));

  const value = React.useMemo(() => ({codeLocations, daemons}), [daemons, codeLocations]);

  return (
    <DeploymentStatusContext.Provider value={value}>{children}</DeploymentStatusContext.Provider>
  );
};
