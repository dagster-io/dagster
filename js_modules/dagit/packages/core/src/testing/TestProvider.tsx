import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {AppContext, AppContextValue} from '../app/AppContext';
import {extractPermissions, PermissionsContext, PermissionsMap} from '../app/Permissions';
import {WebSocketContext} from '../app/WebSocketProvider';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

const testValue = {
  basePath: '',
  rootServerURI: '',
};

const websocketValue = {
  websocketURI: 'ws://foo',
  status: WebSocket.OPEN,
};

interface Props {
  apolloProps?: ApolloTestProps;
  appContextProps?: Partial<AppContextValue>;
  permissionOverrides?: Partial<PermissionsMap>;
  routerProps?: MemoryRouterProps;
}

export const TestProvider: React.FC<Props> = (props) => {
  const {apolloProps, appContextProps, permissionOverrides = {}, routerProps} = props;
  const permissions = React.useMemo(() => {
    const extracted = extractPermissions([]);
    const keys = Object.keys(extracted);
    const values = {};
    for (const key of keys) {
      const override = permissionOverrides[key];
      values[key] = typeof override === 'boolean' ? override : true;
    }
    return {
      rawPermissions: [],
      permissionsMap: values as PermissionsMap,
    };
  }, [permissionOverrides]);

  return (
    <AppContext.Provider value={{...testValue, ...appContextProps}}>
      <WebSocketContext.Provider value={websocketValue}>
        <PermissionsContext.Provider value={permissions}>
          <MemoryRouter {...routerProps}>
            <ApolloTestProvider {...apolloProps} typeDefs={typeDefs}>
              <WorkspaceProvider>{props.children}</WorkspaceProvider>
            </ApolloTestProvider>
          </MemoryRouter>
        </PermissionsContext.Provider>
      </WebSocketContext.Provider>
    </AppContext.Provider>
  );
};
