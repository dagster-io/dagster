import {ComponentProps} from 'react';
import {NavLink, matchPath} from 'react-router-dom';

type MatcherFn = NonNullable<ComponentProps<typeof NavLink>['isActive']>;

export const jobsPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return !!matchPath(pathname, {
    path: ['/jobs', '/locations/:codeLocation/jobs/:jobName'],
  });
};

export const assetsPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    pathname.startsWith('/catalog') ||
    pathname.startsWith('/assets') ||
    pathname.startsWith('/asset-groups') ||
    (pathname.startsWith('/locations') && pathname.includes('/asset-groups/'))
  );
};

export const deploymentPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    pathname.startsWith('/deployment') ||
    (pathname.startsWith('/locations') &&
      !pathname.includes('/asset-groups/') &&
      !automationPathMatcher(_, currentLocation) &&
      !jobsPathMatcher(_, currentLocation))
  );
};

export const locationPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    (pathname.startsWith('/locations') && !pathname.includes('/asset-groups/')) ||
    pathname.startsWith('/health') ||
    pathname.startsWith('/concurrency') ||
    pathname.startsWith('/config')
  );
};

export const automationPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return !!matchPath(pathname, {
    path: [
      '/automation',
      '/locations/:codeLocation/sensors/:sensorName',
      '/locations/:codeLocation/schedules/:scheduleName',
    ],
  });
};
