// Before anything else, set the webpack public path.
import './publicPath';

import {Colors, Icon} from '@blueprintjs/core';
import {App} from '@dagit/core/app/App';
import {createAppCache} from '@dagit/core/app/AppCache';
import {AppProvider} from '@dagit/core/app/AppProvider';
import {AppTopNav} from '@dagit/core/app/AppTopNav';
import * as React from 'react';
import ReactDOM from 'react-dom';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {extractPathPrefix} from './extractPathPrefix';

const pathPrefix = extractPathPrefix();

const config = {
  basePath: pathPrefix,
  origin: process.env.REACT_APP_BACKEND_ORIGIN || document.location.origin,
};

const appCache = createAppCache();

const SettingsLink = styled(Link)`
  background-color: ${Colors.DARK_GRAY1};
  padding: 15px;

  .bp3-icon svg {
    transition: fill 50ms linear;
  }

  &:hover .bp3-icon svg {
    fill: ${Colors.GRAY4};
  }

  &:active .bp3-icon svg {
    fill: ${Colors.GRAY5};
  }
`;

ReactDOM.render(
  <AppProvider appCache={appCache} config={config}>
    <AppTopNav searchPlaceholder="Search…">
      <SettingsLink to="/settings" title="User settings">
        <Icon icon="cog" iconSize={16} color={Colors.GRAY2} />
      </SettingsLink>
    </AppTopNav>
    <App />
  </AppProvider>,
  document.getElementById('root'),
);
