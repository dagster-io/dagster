// Before anything else, set the webpack public path.
import './publicPath';

import {App} from '@dagster-io/dagit-core/app/App';
import {createAppCache} from '@dagster-io/dagit-core/app/AppCache';
import {errorLink, setupErrorToasts} from '@dagster-io/dagit-core/app/AppError';
import {AppProvider} from '@dagster-io/dagit-core/app/AppProvider';
import {AppTopNav} from '@dagster-io/dagit-core/app/AppTopNav';
import {ContentRoot} from '@dagster-io/dagit-core/app/ContentRoot';
import {UserSettingsButton} from '@dagster-io/dagit-core/app/UserSettingsButton';
import {logLink, timeStartLink} from '@dagster-io/dagit-core/app/apolloLinks';
import {DeploymentStatusType} from '@dagster-io/dagit-core/instance/DeploymentStatusProvider';
import * as React from 'react';
import ReactDOM from 'react-dom';

import {CommunityNux} from './NUX/CommunityNux';
import {extractInitializationData} from './extractInitializationData';
import {telemetryLink} from './telemetryLink';

const {pathPrefix, telemetryEnabled} = extractInitializationData();

const apolloLinks = [logLink, errorLink, timeStartLink];

if (telemetryEnabled) {
  apolloLinks.unshift(telemetryLink(pathPrefix));
}
if (process.env.NODE_ENV === 'development') {
  setupErrorToasts();
}

const config = {
  apolloLinks,
  basePath: pathPrefix,
  origin: process.env.REACT_APP_BACKEND_ORIGIN || document.location.origin,
  staticPathRoot: `${pathPrefix}/`,
  telemetryEnabled,
  statusPolling: new Set<DeploymentStatusType>(['code-locations', 'daemons']),
};

const appCache = createAppCache();
const container = document.getElementById('root');

ReactDOM.render(
  <AppProvider appCache={appCache} config={config}>
    <AppTopNav searchPlaceholder="Search…">
      <UserSettingsButton />
    </AppTopNav>
    <App>
      <ContentRoot />
      <CommunityNux />
    </App>
  </AppProvider>,
  container,
);
