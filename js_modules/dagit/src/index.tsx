import '@blueprintjs/core/lib/css/blueprint.css';
import '@blueprintjs/icons/lib/css/blueprint-icons.css';
import '@blueprintjs/select/lib/css/blueprint-select.css';
import '@blueprintjs/table/lib/css/table.css';

import 'src/fonts/fonts.css';

import {ApolloClient, ApolloLink, ApolloProvider} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {createGlobalStyle} from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {App} from 'src/app/App';
import {AppCache} from 'src/app/AppCache';
import {AppErrorLink} from 'src/app/AppError';
import {WEBSOCKET_URI} from 'src/app/DomUtils';
import {formatElapsedTime, patchCopyToRemoveZeroWidthUnderscores, debugLog} from 'src/app/Util';
import {WebsocketStatusProvider} from 'src/app/WebsocketStatus';
import {FontFamily} from 'src/ui/styles';

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
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

ReactDOM.render(
  <WebsocketStatusProvider websocket={websocketClient}>
    <GlobalStyle />
    <ApolloProvider client={client}>
      <App />
    </ApolloProvider>
  </WebsocketStatusProvider>,
  document.getElementById('root') as HTMLElement,
);
