import {Box} from '@dagster-io/ui-components';
import {useHistory} from 'react-router-dom';

import {TopNavLink} from './AppTopNav';
import {DeploymentStatusIcon} from '../../nav/DeploymentStatusIcon';
import {FeatureFlag, featureEnabled} from '../Flags';
import {ShortcutHandler} from '../ShortcutHandler';

export type AppNavLinkType = {
  title: string;
  element: React.ReactNode;
};

export const AppTopNavLinks = ({links}: {links: AppNavLinkType[]}) => {
  return (
    <Box margin={{left: 8}} flex={{direction: 'row', alignItems: 'center', gap: 16}}>
      {links.map((link) => link.element)}
    </Box>
  );
};

export const navLinks = (history: ReturnType<typeof useHistory>) => {
  return [
    {
      title: 'overview' as const,
      element: (
        <ShortcutHandler
          key="overview"
          onShortcut={() => history.push('/overview')}
          shortcutLabel="⌥1"
          shortcutFilter={(e) => e.altKey && e.code === 'Digit1'}
        >
          <TopNavLink to="/overview" data-cy="AppTopNav_StatusLink">
            Overview
          </TopNavLink>
        </ShortcutHandler>
      ),
    },
    {
      title: 'runs' as const,
      element: (
        <ShortcutHandler
          key="runs"
          onShortcut={() => history.push('/runs')}
          shortcutLabel="⌥2"
          shortcutFilter={(e) => e.altKey && e.code === 'Digit2'}
        >
          <TopNavLink to="/runs" data-cy="AppTopNav_RunsLink">
            Runs
          </TopNavLink>
        </ShortcutHandler>
      ),
    },
    {
      title: 'assets' as const,
      element: (
        <ShortcutHandler
          key="assets"
          onShortcut={() => history.push('/assets')}
          shortcutLabel="⌥3"
          shortcutFilter={(e) => e.altKey && e.code === 'Digit3'}
        >
          <TopNavLink
            to={featureEnabled(FeatureFlag.flagUseNewOverviewPage) ? '/assets-overview' : '/assets'}
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
    },
    featureEnabled(FeatureFlag.flagSettingsPage)
      ? {
          title: 'settings' as const,
          element: (
            <ShortcutHandler
              key="settings"
              onShortcut={() => history.push('/settings')}
              shortcutLabel="⌥4"
              shortcutFilter={(e) => e.altKey && e.code === 'Digit4'}
            >
              <TopNavLink
                to="/settings"
                data-cy="AppTopNav_SettingsLink"
                isActive={(_, location) => {
                  const {pathname} = location;
                  return pathname.startsWith('/settings') || pathname.startsWith('/locations');
                }}
              >
                <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                  Settings
                  <DeploymentStatusIcon />
                </Box>
              </TopNavLink>
            </ShortcutHandler>
          ),
        }
      : {
          title: 'deployment' as const,
          element: (
            <ShortcutHandler
              key="deployment"
              onShortcut={() => history.push('/locations')}
              shortcutLabel="⌥4"
              shortcutFilter={(e) => e.altKey && e.code === 'Digit4'}
            >
              <TopNavLink
                to="/locations"
                data-cy="AppTopNav_StatusLink"
                isActive={(_, location) => {
                  const {pathname} = location;
                  return (
                    pathname.startsWith('/locations') ||
                    pathname.startsWith('/health') ||
                    pathname.startsWith('/config')
                  );
                }}
              >
                <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                  Deployment
                  <DeploymentStatusIcon />
                </Box>
              </TopNavLink>
            </ShortcutHandler>
          ),
        },
  ];
};
