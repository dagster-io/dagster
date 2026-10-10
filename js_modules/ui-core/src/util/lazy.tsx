import React, {useContext, useEffect, useMemo, useState} from 'react';

import {RouteContentContext, useUnknownMobileRouteStatus} from '../app/layout/mobileRouteStatus';
import {CompletionType, useTraceDependency} from '../performance/TraceContext';

type ResolvedType<T> = T extends Promise<infer U> ? U : never;

export const lazy = <T extends () => Promise<{default: React.ComponentType<any>}>>(importFn: T) => {
  type ComponentType = ResolvedType<ReturnType<T>>['default'];
  type Props = React.ComponentProps<ComponentType>;

  let promise: Promise<{default: React.ComponentType<any>}> | null = null;
  // Once loaded, later mounts render synchronously instead of showing the placeholder first.
  let loaded: React.ComponentType<any> | null = null;
  const LazyComponent = (props: Props & {_placeholder?: React.ReactNode}) => {
    const [Component, setComponent] = useState<any | null>(() => loaded);
    const [errored, setErrored] = useState(false);
    const dependency = useTraceDependency('LazyImport');

    const routeContent = useContext(RouteContentContext);
    const isRouteContent = routeContent?.type === LazyComponent;
    useUnknownMobileRouteStatus(isRouteContent && !Component && !errored, routeContent?.pathname);

    useMemo(() => {
      if (!promise) {
        promise = importFn();
      }
      promise.then(
        (res) => {
          loaded = res.default;
          setComponent(() => res.default);
        },
        () => {
          setErrored(true);
        },
      );
    }, []);
    useEffect(() => {
      if (Component) {
        dependency.completeDependency(CompletionType.SUCCESS);
      } else if (errored) {
        dependency.completeDependency(CompletionType.ERROR);
      }
    }, [dependency, errored, Component]);
    return Component ? <Component {...props} /> : props._placeholder;
  };
  return LazyComponent;
};
