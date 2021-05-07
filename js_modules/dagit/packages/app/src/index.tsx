// Before anything else, set the webpack public path.
import './publicPath';

import {App} from '@dagit/core/app/App';
import {AppProvider} from '@dagit/core/app/AppProvider';
import {AppTopNav} from '@dagit/core/app/AppTopNav';
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
