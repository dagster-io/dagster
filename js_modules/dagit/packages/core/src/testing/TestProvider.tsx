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

export const PERMISSIONS_ALLOW_ALL: PermissionsFromJSON = {
  launch_pipeline_execution: true,
  launch_pipeline_reexecution: true,
  start_schedule: true,
  stop_running_schedule: true,
  edit_sensor: true,
  terminate_pipeline_execution: true,
  delete_pipeline_run: true,
  reload_repository_location: true,
  reload_workspace: true,
  wipe_assets: true,
  launch_partition_backfill: true,
  cancel_partition_backfill: true,
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
  permissionOverrides?: {[permission: string]: boolean};
  routerProps?: MemoryRouterProps;
}

export const TestProvider: React.FC<Props> = (props) => {
  const {apolloProps, appContextProps, permissionOverrides, routerProps} = props;
  const permissions: PermissionFragment[] = React.useMemo(() => {
    return Object.keys(PERMISSIONS_ALLOW_ALL).map((permission) => {
      const override = permissionOverrides ? permissionOverrides[permission] : null;
      const value = typeof override === 'boolean' ? override : true;
      return {__typename: 'Permission', permission, value};
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
