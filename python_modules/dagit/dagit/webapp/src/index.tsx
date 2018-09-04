import * as React from "react";
import * as ReactDOM from "react-dom";
import { injectGlobal } from "styled-components";
import ApolloClient from "apollo-boost";
import {
  InMemoryCache,
  IntrospectionFragmentMatcher
} from "apollo-cache-inmemory";
import { ApolloProvider } from "react-apollo";
import App from "./App";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import introspectionQueryResultData from "./schema.json";

const fragmentMatcher = new IntrospectionFragmentMatcher({
  introspectionQueryResultData: {
    __schema: introspectionQueryResultData
  }
});

const cache = new InMemoryCache({ fragmentMatcher });

const client = new ApolloClient({
  cache,
  uri: process.env.REACT_APP_GRAPHQL_URI || "/graphql"
});

ReactDOM.render(
  <ApolloProvider client={client}>
    <App />
  </ApolloProvider>,
  document.getElementById("root") as HTMLElement
);

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
