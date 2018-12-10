import * as React from "react";
import * as ReactDOM from "react-dom";
import { injectGlobal } from "styled-components";
import ApolloClient from "apollo-client";
import { ApolloProvider } from "react-apollo";
import { SubscriptionClient } from "subscriptions-transport-ws";
import { WebSocketLink } from "apollo-link-ws";
import App from "./App";
import ApiResultRenderer from "./ApiResultRenderer";
import AppCache from "./AppCache";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import "@blueprintjs/select/lib/css/blueprint-select.css";

const websocketClient = new SubscriptionClient(
  process.env.REACT_APP_GRAPHQL_URI || `ws://${document.location.host}/graphql`,
  {
    reconnect: true
  }
);

const client = new ApolloClient({
  cache: AppCache,
  link: new WebSocketLink(websocketClient)
});

if (process.env.REACT_APP_RENDER_API_RESULTS) {
  ReactDOM.render(
    <ApolloProvider client={client}>
      <ApiResultRenderer />
    </ApolloProvider>,
    document.getElementById("root") as HTMLElement
  );
} else {
  ReactDOM.render(
    <ApolloProvider client={client}>
      <App />
    </ApolloProvider>,
    document.getElementById("root") as HTMLElement
  );
}

injectGlobal`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    max-width: 100%;
    min-height: 100%;
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
    font-family: sans-serif;
  }
`;
