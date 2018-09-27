import * as React from "react";
import * as ReactDOM from "react-dom";
import { injectGlobal } from "styled-components";
import ApolloClient from "apollo-boost";
import { ApolloProvider } from "react-apollo";
import App from "./App";
import AppCache from "./AppCache";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import "@blueprintjs/select/lib/css/blueprint-select.css";

const client = new ApolloClient({
  cache: AppCache,
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

  /* Prevent Blueprint's Select dropdowns from having duplicate icons */
  .bp3-popover-content {
    svg[data-icon] { display: none; }
  }
`;
