import '../fonts/fonts.css';

import {
  ApolloLink,
  ApolloClient,
  ApolloProvider,
  HttpLink,
  InMemoryCache,
  split,
} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {getMainDefinition} from '@apollo/client/utilities';
import {
  ColorsWIP,
  GlobalDialogStyle,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalToasterStyle,
  GlobalTooltipStyle,
  FontFamily,
} from '@dagster-io/ui';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {AppContext} from './AppContext';
import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {LayoutProvider} from './LayoutProvider';
import {PermissionsProvider} from './Permissions';
import {patchCopyToRemoveZeroWidthUnderscores} from './Util';
import {WebSocketProvider} from './WebSocketProvider';
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
    color: ${ColorsWIP.Gray800};
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${ColorsWIP.Link};
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

  body, input, select, textarea {
    font-family: ${FontFamily.default};
  }

  button {
    font-family: inherit;
  }

  code, pre {
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  .material-icons {
    display: block;
  }

  /* todo dish: Remove these when we have buttons updated. */

  .bp3-button .material-icons {
    position: relative;
    top: 1px;
  }

  .bp3-button:disabled .material-icons {
    color: ${ColorsWIP.Gray300}
  }
`;

export interface AppProviderProps {
  appCache: InMemoryCache;
  config: {
    apolloLinks: ApolloLink[];
    basePath?: string;
    telemetryEnabled?: boolean;
    headers?: {[key: string]: string};
    origin: string;
  };
}

export const AppProvider: React.FC<AppProviderProps> = (props) => {
  const {appCache, config} = props;
  const {apolloLinks, basePath = '', headers = {}, origin, telemetryEnabled = false} = config;

  const graphqlPath = `${basePath}/graphql`;
  const rootServerURI = `${origin}${basePath}`;
  const websocketURI = `${rootServerURI.replace(/^http/, 'ws')}/graphql`;

  // Ensure that we use the same `headers` value.
  const headersAsString = JSON.stringify(headers);
  const headerObject = React.useMemo(() => JSON.parse(headersAsString), [headersAsString]);

  const websocketClient = React.useMemo(
    () =>
      new SubscriptionClient(websocketURI, {
        reconnect: true,
        connectionParams: {...headerObject},
      }),
    [headerObject, websocketURI],
  );

  const apolloClient = React.useMemo(() => {
    // Subscriptions use WebSocketLink, queries & mutations use HttpLink.
    const splitLink = split(
      ({query}) => {
        const definition = getMainDefinition(query);
        return definition.kind === 'OperationDefinition' && definition.operation === 'subscription';
      },
      new WebSocketLink(websocketClient),
      new HttpLink({uri: graphqlPath, headers: headerObject}),
    );

    return new ApolloClient({
      cache: appCache,
      link: ApolloLink.from([...apolloLinks, splitLink]),
    });
  }, [apolloLinks, appCache, graphqlPath, headerObject, websocketClient]);

  const appContextValue = React.useMemo(
    () => ({
      basePath,
      rootServerURI,
      telemetryEnabled,
    }),
    [basePath, rootServerURI, telemetryEnabled],
  );

  return (
    <AppContext.Provider value={appContextValue}>
      <WebSocketProvider websocketClient={websocketClient}>
        <GlobalStyle />
        <GlobalToasterStyle />
        <GlobalTooltipStyle />
        <GlobalPopoverStyle />
        <GlobalDialogStyle />
        <GlobalSuggestStyle />
        <ApolloProvider client={apolloClient}>
          <PermissionsProvider>
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
          </PermissionsProvider>
        </ApolloProvider>
      </WebSocketProvider>
    </AppContext.Provider>
  );
};
