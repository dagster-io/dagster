import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {AppContext, AppContextValue} from '../app/AppContext';
import {PermissionsContext, PermissionsFromJSON} from '../app/Permissions';
import {WebSocketContext, WebSocketContextType} from '../app/WebSocketProvider';
import {AnalyticsContext} from '../app/analytics';
import {PermissionFragment} from '../app/types/PermissionFragment';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

const DEFAULT_PERMISSIONS = {
  enabled: true,
  disabledReason: '',
};

export const PERMISSIONS_ALLOW_ALL: PermissionsFromJSON = {
  launch_pipeline_execution: DEFAULT_PERMISSIONS,
  launch_pipeline_reexecution: DEFAULT_PERMISSIONS,
  start_schedule: DEFAULT_PERMISSIONS,
  stop_running_schedule: DEFAULT_PERMISSIONS,
  edit_sensor: DEFAULT_PERMISSIONS,
  terminate_pipeline_execution: DEFAULT_PERMISSIONS,
  delete_pipeline_run: DEFAULT_PERMISSIONS,
  reload_repository_location: DEFAULT_PERMISSIONS,
  reload_workspace: DEFAULT_PERMISSIONS,
  wipe_assets: DEFAULT_PERMISSIONS,
  launch_partition_backfill: DEFAULT_PERMISSIONS,
  cancel_partition_backfill: DEFAULT_PERMISSIONS,
};

const testValue: AppContextValue = {
  basePath: '',
  rootServerURI: '',
  staticPathRoot: '/',
  telemetryEnabled: false,
};

const websocketValue: WebSocketContextType = {
  availability: 'available',
  status: WebSocket.OPEN,
  disabled: false,
};

interface Props {
  apolloProps?: ApolloTestProps;
  appContextProps?: Partial<AppContextValue>;
  permissionOverrides?: {[permission: string]: {enabled: boolean; disabledReason: string | null}};
  routerProps?: MemoryRouterProps;
}

export const TestProvider: React.FC<Props> = (props) => {
  const {apolloProps, appContextProps, permissionOverrides, routerProps} = props;
  const permissions: PermissionFragment[] = React.useMemo(() => {
    return Object.keys(PERMISSIONS_ALLOW_ALL).map((permission) => {
      const override = permissionOverrides ? permissionOverrides[permission] : null;
      const value = override ? override.enabled : true;
      const disabledReason = override ? override.disabledReason : null;
      return {__typename: 'Permission', permission, value, disabledReason};
    });
  }, [permissionOverrides]);

  const analytics = React.useMemo(
    () => ({
      page: () => {},
      track: () => {},
    }),
    [],
  );

  return (
    <AppContext.Provider value={{...testValue, ...appContextProps}}>
      <WebSocketContext.Provider value={websocketValue}>
        <PermissionsContext.Provider value={permissions}>
          <AnalyticsContext.Provider value={analytics}>
            <MemoryRouter {...routerProps}>
              <ApolloTestProvider {...apolloProps} typeDefs={typeDefs}>
                <WorkspaceProvider>{props.children}</WorkspaceProvider>
              </ApolloTestProvider>
            </MemoryRouter>
          </AnalyticsContext.Provider>
        </PermissionsContext.Provider>
      </WebSocketContext.Provider>
    </AppContext.Provider>
  );
};
