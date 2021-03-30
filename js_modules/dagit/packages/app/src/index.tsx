import {App, AppProvider, AppTopNav} from '@dagit/core';
import * as React from 'react';
import ReactDOM from 'react-dom';

const APP_PATH_PREFIX =
  document.querySelector('meta[name=dagit-path-prefix]')?.getAttribute('content') || '';

const config = {
  basePath: APP_PATH_PREFIX,
  graphqlURI: process.env.REACT_APP_GRAPHQL_URI || '',
};

ReactDOM.render(
  <AppProvider config={config}>
    <AppTopNav searchPlaceholder="Search…" />
    <App />
  </AppProvider>,
  document.getElementById('root'),
);
