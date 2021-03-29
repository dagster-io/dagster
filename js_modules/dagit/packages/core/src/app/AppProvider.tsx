import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';
import '@blueprintjs/popover2/lib/css/blueprint-popover2.css';

import {ApolloLink, ApolloClient, ApolloProvider} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import {createGlobalStyle} from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {FontFamily} from '../ui/styles';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {AppCache} from './AppCache';
import {AppErrorLink} from './AppError';
import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {CustomTooltipProvider} from './CustomTooltipProvider';
import {APP_PATH_PREFIX, WEBSOCKET_URI} from './DomUtils';
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

const websocketClient = new SubscriptionClient(WEBSOCKET_URI, {
  reconnect: true,
  lazy: true,
});

const timeStartLink = new ApolloLink((operation, forward) => {
  operation.setContext({start: performance.now()});
  return forward(operation);
});

const logLink = new ApolloLink((operation, forward) => {
  return forward(operation).map((data) => {
    const time = performance.now() - operation.getContext().start;
    debugLog(`${operation.operationName} took ${formatElapsedTime(time)}`, {operation, data});
    return data;
  });
});

const client = new ApolloClient({
  cache: AppCache,
  link: ApolloLink.from([
    logLink,
    AppErrorLink(),
    timeStartLink,
    new WebSocketLink(websocketClient),
  ]),
});

export const AppProvider: React.FC = (props) => (
  <WebsocketStatusProvider websocket={websocketClient}>
    <GlobalStyle />
    <ApolloProvider client={client}>
      <BrowserRouter basename={APP_PATH_PREFIX}>
        <TimezoneProvider>
          <WorkspaceProvider>
            <CustomConfirmationProvider>{props.children}</CustomConfirmationProvider>
            <CustomTooltipProvider />
            <CustomAlertProvider />
          </WorkspaceProvider>
        </TimezoneProvider>
      </BrowserRouter>
    </ApolloProvider>
  </WebsocketStatusProvider>
);
