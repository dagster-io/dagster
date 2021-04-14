// Before anything else, set the webpack public path.
import './publicPath';

import {App, AppProvider, AppTopNav} from '@dagit/core';
import * as React from 'react';
import ReactDOM from 'react-dom';

import {extractPathPrefix} from './extractPathPrefix';

const pathPrefix = extractPathPrefix();

const config = {
  basePath: pathPrefix,
  graphqlURI: process.env.REACT_APP_GRAPHQL_URI || '',
};

ReactDOM.render(
  <AppProvider config={config}>
    <AppTopNav searchPlaceholder="Search…" />
    <App />
  </AppProvider>,
  document.getElementById('root'),
);
