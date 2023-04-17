import {useQuery} from '@apollo/client';
import * as React from 'react';

import {useCodeLocationsStatus} from '../nav/useCodeLocationsStatus';

import {AUTOMATERIALIZE_PAUSED_QUERY} from './DaemonList';
import {StatusAndMessage} from './DeploymentStatusType';
import {
  GetAutoMaterializePausedQuery,
  GetAutoMaterializePausedQueryVariables,
} from './types/DaemonList.types';
import {useDaemonStatus} from './useDaemonStatus';

export type DeploymentStatusType = 'code-locations' | 'daemons';

type DeploymentStatus = {
  codeLocations: StatusAndMessage | null;
  daemons: StatusAndMessage | null;
  autoMaterialization: StatusAndMessage | null;
};

export const DeploymentStatusContext = React.createContext<DeploymentStatus>({
  codeLocations: null,
  daemons: null,
  autoMaterialization: null,
});

interface Props {
  children: React.ReactNode;
  include: Set<DeploymentStatusType>;
}

export const DeploymentStatusProvider: React.FC<Props> = (props) => {
  const {children, include} = props;

  const codeLocations = useCodeLocationsStatus(!include.has('code-locations'));
  const daemons = useDaemonStatus(!include.has('daemons'));
  const autoMaterialization = useAutoMaterializationStatus();

  const value = React.useMemo(() => ({codeLocations, daemons, autoMaterialization}), [
    daemons,
    codeLocations,
    autoMaterialization,
  ]);

  return (
    <DeploymentStatusContext.Provider value={value}>{children}</DeploymentStatusContext.Provider>
  );
};

function useAutoMaterializationStatus() {
  const {data} = useQuery<GetAutoMaterializePausedQuery, GetAutoMaterializePausedQueryVariables>(
    AUTOMATERIALIZE_PAUSED_QUERY,
  );
  if (data?.instance.autoMaterializePaused) {
    return {
      type: 'warning' as const,
      content: <span>Auto-materialization is paused</span>,
    };
  }
  return null;
}
