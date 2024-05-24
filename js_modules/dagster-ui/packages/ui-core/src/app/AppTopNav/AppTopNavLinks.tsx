import {Box} from '@dagster-io/ui-components';
import {ReactNode} from 'react';
import {useHistory} from 'react-router-dom';

import {TopNavLink} from './AppTopNav';
import {
  assetsPathMatcher,
  automationPathMatcher,
  jobsPathMatcher,
  locationPathMatcher,
  settingsPathMatcher,
} from './activePathMatchers';
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
  const overview = {
    key: 'overview',
    path: '/overview',
    element: (
      <TopNavLink to="/overview" data-cy="AppTopNav_StatusLink">
        Overview
      </TopNavLink>
    ),
  };

  const runs = {
    key: 'runs',
    path: '/runs',
    element: (
      <TopNavLink to="/runs" data-cy="AppTopNav_RunsLink">
        Runs
      </TopNavLink>
    ),
  };

  const jobs = {
    key: 'jobs',
    path: '/jobs',
    element: (
      <TopNavLink to="/jobs" data-cy="AppTopNav_JobsLink" isActive={jobsPathMatcher}>
        Jobs
      </TopNavLink>
    ),
  };

  const assets = {
    key: 'assets',
    path: '/assets',
    element: (
      <TopNavLink to="/assets" data-cy="AppTopNav_AssetsLink" isActive={assetsPathMatcher}>
        Assets
      </TopNavLink>
    ),
  };

  const automation = {
    key: 'automation',
    path: '/automation',
    element: (
      <TopNavLink
        to="/automation"
        data-cy="AppTopNav_AutomationLink"
        isActive={automationPathMatcher}
      >
        Automation
      </TopNavLink>
    ),
  };

  const settings = {
    key: 'settings',
    path: '/settings',
    element: (
      <TopNavLink to="/settings" data-cy="AppTopNav_SettingsLink" isActive={settingsPathMatcher}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
          Settings
          <DeploymentStatusIcon />
        </Box>
      </TopNavLink>
    ),
  };

  const deployment = {
    key: 'deployment',
    path: '/locations',
    element: (
      <TopNavLink to="/locations" data-cy="AppTopNav_StatusLink" isActive={locationPathMatcher}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
          Deployment
          <DeploymentStatusIcon />
        </Box>
      </TopNavLink>
    ),
  };

  if (featureEnabled(FeatureFlag.flagSettingsPage)) {
    return [overview, assets, jobs, automation, runs, settings];
  }

  return [overview, runs, assets, deployment];
};
