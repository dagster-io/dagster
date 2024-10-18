import {Box} from '@dagster-io/ui-components';
import {ReactElement} from 'react';
import {useHistory} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {TopNavLink} from './AppTopNav';
import {
  assetsPathMatcher,
  automationPathMatcher,
  deploymentPathMatcher,
  jobsPathMatcher,
  locationPathMatcher,
} from './activePathMatchers';
import {JobStateForNav} from './useJobStateForNav';
import {DeploymentStatusIcon} from '../../nav/DeploymentStatusIcon';
import {featureEnabled} from '../Flags';
import {ShortcutHandler} from '../ShortcutHandler';

export type AppNavLinkType = {
  key: string;
  path: string;
  element: ReactElement;
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

type Config = {
  jobState?: JobStateForNav;
};

export const navLinks = (config: Config): AppNavLinkType[] => {
  const {jobState = 'unknown'} = config;

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

  if (!featureEnabled(FeatureFlag.flagLegacyNav)) {
    const jobs =
      jobState === 'has-jobs'
        ? {
            key: 'jobs',
            path: '/jobs',
            element: (
              <TopNavLink to="/jobs" data-cy="AppTopNav_JobsLink" isActive={jobsPathMatcher}>
                Jobs
              </TopNavLink>
            ),
          }
        : null;

    const deployment = {
      key: 'deployment',
      path: '/deployment',
      element: (
        <TopNavLink
          to="/deployment"
          data-cy="AppTopNav_DeploymentLink"
          isActive={deploymentPathMatcher}
        >
          <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
            Deployment
            <DeploymentStatusIcon />
          </Box>
        </TopNavLink>
      ),
    };

    return [overview, runs, assets, jobs, automation, deployment].filter(
      (link): link is AppNavLinkType => !!link,
    );
  }

  const deployment = {
    key: 'locations',
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

  return [overview, runs, assets, deployment];
};
