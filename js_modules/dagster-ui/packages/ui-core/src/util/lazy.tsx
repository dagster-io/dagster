import React, {useEffect, useMemo, useState} from 'react';

import {CompletionType, useTraceDependency} from '../performance/TraceContext';

type ResolvedType<T> = T extends Promise<infer U> ? U : never;

export const lazy = <T extends () => Promise<{default: React.ComponentType<any>}>>(importFn: T) => {
  type ComponentType = ResolvedType<ReturnType<T>>['default'];
  type Props = React.ComponentProps<ComponentType>;

  let promise: Promise<{default: React.ComponentType<any>}> | null = null;
  return (props: Props & {_placeholder?: React.ReactNode}) => {
    const [Component, setComponent] = useState<any | null>(null);
    const [errored, setErrored] = useState(false);
    const dependency = useTraceDependency('LazyImport');
    useMemo(() => {
      if (!promise) {
        promise = importFn();
      }
      promise.then(
        (res) => {
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
};
