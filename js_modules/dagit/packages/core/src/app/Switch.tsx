import * as React from 'react';
import {matchPath, useLocation} from 'react-router-dom';

import {RouteConfig} from './types';

interface Props<P> {
  permissions: P;
  routes: RouteConfig<any, P>[];
}

export const Switch = <P,>(props: Props<P>) => {
  const location = useLocation();
  const {permissions, routes} = props;

  for (let ii = 0; ii < routes.length; ii++) {
    const route = routes[ii];
    const {isAvailable, path, render} = route;

    // On a permission failure, continue. If no `isAvailable` is defined, the route
    // is considered to be available.
    if (isAvailable && !isAvailable(permissions)) {
      continue;
    }

    const match = matchPath(location.pathname, {path});
    if (match) {
      if (render) {
        return render({match, permissions});
      }

      if (route.routes) {
        return <Switch permissions={permissions} routes={route.routes} />;
      }
    }
  }

  // No matches in this list of routes, and no fallback supplied.
  // todo dish: Proper 404
  return <div>404</div>;
};
