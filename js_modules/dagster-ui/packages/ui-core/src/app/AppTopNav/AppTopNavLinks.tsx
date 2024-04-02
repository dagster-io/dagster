import {Box} from '@dagster-io/ui-components';
import {ReactNode} from 'react';
import {useHistory} from 'react-router-dom';

import {TopNavLink} from './AppTopNav';
import {assetsPathMatcher, locationPathMatcher, settingsPathMatcher} from './activePathMatchers';
import {DeploymentStatusIcon} from '../../nav/DeploymentStatusIcon';
import {FeatureFlag, featureEnabled} from '../Flags';
import {ShortcutHandler} from '../ShortcutHandler';

export type AppNavLinkType = {
  key: string;
  path: string;
  element: ReactNode;
};

export const AppTopNavLinks = ({links}: {links: AppNavLinkType[]}) => {
  const history = useHistory();
  return (
    <Box margin={{left: 8}} flex={{direction: 'row', alignItems: 'center', gap: 16}}>
      {links.map((link, ii) => {
        const {key, path, element} = link;
        return (
          <ShortcutHandler
            key={key}
            onShortcut={() => history.push(path)}
            shortcutLabel={`⌥${ii + 1}`}
            shortcutFilter={(e) => e.altKey && e.code === `Digit${ii + 1}`}
          >
            {element}
          </ShortcutHandler>
        );
      })}
    </Box>
  );
};

export const navLinks = () => {
  return [
    {
      key: 'overview',
      path: '/overview',
      element: (
        <TopNavLink to="/overview" data-cy="AppTopNav_StatusLink">
          Overview
        </TopNavLink>
      ),
    },
    {
      key: 'runs',
      path: '/runs',
      element: (
        <TopNavLink to="/runs" data-cy="AppTopNav_RunsLink">
          Runs
        </TopNavLink>
      ),
    },
    {
      key: 'assets',
      path: '/assets',
      element: (
        <TopNavLink
          to="/assets"
          data-cy="AppTopNav_AssetsLink"
          isActive={assetsPathMatcher}
          exact={false}
        >
          Assets
        </TopNavLink>
      ),
    },
    featureEnabled(FeatureFlag.flagSettingsPage)
      ? {
          key: 'settings',
          path: '/settings',
          element: (
            <TopNavLink
              to="/settings"
              data-cy="AppTopNav_SettingsLink"
              isActive={settingsPathMatcher}
            >
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                Settings
                <DeploymentStatusIcon />
              </Box>
            </TopNavLink>
          ),
        }
      : {
          key: 'deployment',
          path: '/locations',
          element: (
            <TopNavLink
              to="/locations"
              data-cy="AppTopNav_StatusLink"
              isActive={locationPathMatcher}
            >
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                Deployment
                <DeploymentStatusIcon />
              </Box>
            </TopNavLink>
          ),
        },
  ];
};
