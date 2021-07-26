import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';
import '@blueprintjs/popover2/lib/css/blueprint-popover2.css';

import {
  split,
  ApolloLink,
  ApolloClient,
  ApolloProvider,
  HttpLink,
  InMemoryCache,
} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {getMainDefinition} from '@apollo/client/utilities';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {FontFamily} from '../ui/styles';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {AppContext} from './AppContext';
import {AppErrorLink} from './AppError';
import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {LayoutProvider} from './LayoutProvider';
import {PermissionsFromJSON} from './Permissions';
import {formatElapsedTime, patchCopyToRemoveZeroWidthUnderscores, debugLog} from './Util';
import {WebsocketStatusProvider} from './WebsocketStatus';
import {TimezoneProvider} from './time/TimezoneContext';

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    color: ${Colors.DARK_GRAY4};
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  #root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, button, input, select, textarea {
    font-family: ${FontFamily.default};
  }

  code, pre {
    font-family: ${FontFamily.monospace};
  }
`;

interface Props {
  appCache: InMemoryCache;
  config: {
    basePath?: string;
    headers?: {[key: string]: string};
    origin: string;
    permissions: PermissionsFromJSON;
  };
}

export const AppProvider: React.FC<Props> = (props) => {
  const {appCache, config} = props;
  const {basePath = '', headers, origin, permissions} = config;

  const graphqlPath = `${basePath}/graphql`;
  const rootServerURI = `${origin}${basePath}`;
  const websocketURI = `${rootServerURI.replace(/^http/, 'ws')}/graphql`;

  const websocketClient = React.useMemo(() => {
    return new SubscriptionClient(websocketURI, {
      reconnect: true,
      connectionParams: {...headers},
    });
  }, [headers, websocketURI]);

  const apolloClient = React.useMemo(() => {
    const logLink = new ApolloLink((operation, forward) =>
      forward(operation).map((data) => {
        const time = performance.now() - operation.getContext().start;
        debugLog(`${operation.operationName} took ${formatElapsedTime(time)}`, {operation, data});
        return data;
      }),
    );

    const timeStartLink = new ApolloLink((operation, forward) => {
      operation.setContext({start: performance.now()});
      return forward(operation);
    });

    const httpLink = new HttpLink({uri: graphqlPath, headers});
    const websocketLink = new WebSocketLink(websocketClient);

    // subscriptions should use the websocket link; queries & mutations should use HTTP
    const splitLink = split(
      ({query}) => {
        const definition = getMainDefinition(query);
        return definition.kind === 'OperationDefinition' && definition.operation === 'subscription';
      },
      websocketLink,
      httpLink,
    );

    return new ApolloClient({
      cache: appCache,
      link: ApolloLink.from([logLink, AppErrorLink(), timeStartLink, splitLink]),
    });
  }, [appCache, graphqlPath, headers, websocketClient]);

  const appContextValue = React.useMemo(
    () => ({
      basePath,
      permissions,
      rootServerURI,
      websocketURI,
    }),
    [basePath, permissions, rootServerURI, websocketURI],
  );

  return (
    <AppContext.Provider value={appContextValue}>
      <WebsocketStatusProvider websocket={websocketClient}>
        <GlobalStyle />
        <ApolloProvider client={apolloClient}>
          <BrowserRouter basename={basePath || ''}>
            <TimezoneProvider>
              <WorkspaceProvider>
                <CustomConfirmationProvider>
                  <LayoutProvider>{props.children}</LayoutProvider>
                </CustomConfirmationProvider>
                <CustomTooltipProvider />
                <CustomAlertProvider />
              </WorkspaceProvider>
            </TimezoneProvider>
          </BrowserRouter>
        </ApolloProvider>
      </WebsocketStatusProvider>
    </AppContext.Provider>
  );
};
