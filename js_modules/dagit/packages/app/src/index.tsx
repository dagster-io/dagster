// Before anything else, set the webpack public path.
import './publicPath';

import {App} from '@dagit/core/app/App';
import {createAppCache} from '@dagit/core/app/AppCache';
import {errorLink} from '@dagit/core/app/AppError';
import {AppProvider} from '@dagit/core/app/AppProvider';
import {AppTopNav, AppTopNavTabs} from '@dagit/core/app/AppTopNav';
import {ContentRoot} from '@dagit/core/app/ContentRoot';
import {logLink, timeStartLink} from '@dagit/core/app/apolloLinks';
import {ColorsWIP} from '@dagit/core/ui/Colors';
import {IconWIP, IconWrapper} from '@dagit/core/ui/Icon';
import * as React from 'react';
import ReactDOM from 'react-dom';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {extractPathPrefix} from './extractPathPrefix';

const pathPrefix = extractPathPrefix();

const apolloLinks = [logLink, errorLink, timeStartLink];

const config = {
  apolloLinks,
  basePath: pathPrefix,
  origin: process.env.REACT_APP_BACKEND_ORIGIN || document.location.origin,
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
      <AppTopNavTabs />
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
