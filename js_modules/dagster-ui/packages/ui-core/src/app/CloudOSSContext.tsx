import React from 'react';
import {useHistory} from 'react-router-dom';

import {TopNavLink} from './AppTopNav/AppTopNav';
import {ShortcutHandler} from './ShortcutHandler';

export const getAssetsTopNavLink = (history: ReturnType<typeof useHistory>) => ({
  title: 'assets',
  element: (
    <ShortcutHandler
      key="assets"
      onShortcut={() => history.push('/assets')}
      shortcutLabel="⌥3"
      shortcutFilter={(e) => e.altKey && e.code === 'Digit3'}
    >
      <TopNavLink
        to="/assets"
        data-cy="AppTopNav_AssetsLink"
        isActive={(_, location) => {
          const {pathname} = location;
          return pathname.startsWith('/assets') || pathname.startsWith('/asset-groups');
        }}
        exact={false}
      >
        Assets
      </TopNavLink>
    </ShortcutHandler>
  ),
});

export const CloudOSSContext = React.createContext<{
  isBranchDeployment: boolean;
  getAssetsTopNavLink: (history: ReturnType<typeof useHistory>) => {
    title: string;
    element: React.ReactNode;
  };
}>({
  isBranchDeployment: false,
  getAssetsTopNavLink,
});
