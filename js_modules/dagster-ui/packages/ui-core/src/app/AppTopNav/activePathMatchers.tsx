import {ComponentProps} from 'react';
import {NavLink} from 'react-router-dom';

type MatcherFn = NonNullable<ComponentProps<typeof NavLink>['isActive']>;

export const assetsPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    pathname.startsWith('/catalog') ||
    pathname.startsWith('/assets') ||
    pathname.startsWith('/asset-groups') ||
    (pathname.startsWith('/locations') && pathname.includes('/asset-groups/'))
  );
};

export const settingsPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    pathname.startsWith('/settings') ||
    (pathname.startsWith('/locations') && !pathname.includes('/asset-groups/'))
  );
};

export const locationPathMatcher: MatcherFn = (_, currentLocation) => {
  const {pathname} = currentLocation;
  return (
    (pathname.startsWith('/locations') && !pathname.includes('/asset-groups/')) ||
    pathname.startsWith('/health') ||
    pathname.startsWith('/config')
  );
};
