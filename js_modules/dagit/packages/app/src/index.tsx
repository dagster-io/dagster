// Before anything else, set the webpack public path.
import './publicPath';

import {App} from '@dagit/core/app/App';
import {createAppCache} from '@dagit/core/app/AppCache';
import {AppProvider} from '@dagit/core/app/AppProvider';
import {AppTopNav} from '@dagit/core/app/AppTopNav';
import {PermissionsFromJSON, PERMISSIONS_ALLOW_ALL} from '@dagit/core/app/Permissions';
import * as React from 'react';
import ReactDOM from 'react-dom';

import {extractPathPrefix} from './extractPathPrefix';

const pathPrefix = extractPathPrefix();

const permissionsElement = document.getElementById('permissions');

const identity: {permissions: PermissionsFromJSON} = permissionsElement
  ? JSON.parse(permissionsElement.textContent || '')
  : {
      permissions: {},
    };

const permissions =
  identity.permissions === '[permissions_here]' ? PERMISSIONS_ALLOW_ALL : identity.permissions;

const config = {
  basePath: pathPrefix,
  graphqlURI: process.env.REACT_APP_GRAPHQL_URI || '',
  permissions,
};

const appCache = createAppCache();

ReactDOM.render(
  <AppProvider appCache={appCache} config={config}>
    <AppTopNav searchPlaceholder="Search…" />
    <App />
  </AppProvider>,
  document.getElementById('root'),
);
