// Before anything else, set the webpack public path.
import './publicPath';

import {App} from '@dagster-io/dagit-core/app/App';
import {createAppCache} from '@dagster-io/dagit-core/app/AppCache';
import {errorLink} from '@dagster-io/dagit-core/app/AppError';
import {AppProvider} from '@dagster-io/dagit-core/app/AppProvider';
import {AppTopNav} from '@dagster-io/dagit-core/app/AppTopNav';
import {ContentRoot} from '@dagster-io/dagit-core/app/ContentRoot';
import {logLink, timeStartLink} from '@dagster-io/dagit-core/app/apolloLinks';
import {ColorsWIP} from '@dagster-io/dagit-core/ui/Colors';
import {IconWIP, IconWrapper} from '@dagster-io/dagit-core/ui/Icon';
import * as React from 'react';
import ReactDOM from 'react-dom';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {extractInitializationData} from './extractInitializationData';
import {telemetryLink} from './telemetryLink';

const {pathPrefix, telemetryEnabled} = extractInitializationData();

const apolloLinks = [logLink, errorLink, timeStartLink];

if (telemetryEnabled) {
  apolloLinks.unshift(telemetryLink(pathPrefix));
}

const config = {
  apolloLinks,
  basePath: pathPrefix,
  origin: process.env.REACT_APP_BACKEND_ORIGIN || document.location.origin,
  telemetryEnabled,
};

const appCache = createAppCache();

const SettingsLink = styled(Link)`
  padding: 24px;

  ${IconWrapper} {
    transition: background 50ms linear;
  }

  &:hover ${IconWrapper} {
    background: ${ColorsWIP.White};
  }

  &:active ${IconWrapper} {
    background: ${ColorsWIP.White};
  }
`;

ReactDOM.render(
  <AppProvider appCache={appCache} config={config}>
    <AppTopNav searchPlaceholder="Search…">
      <SettingsLink to="/settings" title="User settings">
        <IconWIP name="settings" color={ColorsWIP.Gray200} />
      </SettingsLink>
    </AppTopNav>
    <App>
      <ContentRoot />
    </App>
  </AppProvider>,
  document.getElementById('root'),
);
