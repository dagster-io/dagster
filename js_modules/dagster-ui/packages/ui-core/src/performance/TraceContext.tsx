import {QueryResult} from '@apollo/client';
import {ReactNode, createContext, useContext, useLayoutEffect, useMemo} from 'react';

type TraceContextType = {
  createDependency: (_name: string) => Dependency | null;
  addDependency: (_dep: Dependency | null) => void;
  cancelDependency: (_dep: Dependency | null) => void;
  completeDependency: (_dep: Dependency | null) => void;
  completeDependencyWithError: (_dep: Dependency | null) => void;
};

export const TraceContext = createContext<TraceContextType>({
  createDependency: (_name: string) => null,
  addDependency: (_dep) => {},
  cancelDependency: (_dep) => {},
  completeDependency: (_dep) => {},
  completeDependencyWithError: () => {},
});

/**
 * Use this to wrap child react components who should not count
 * toward display done. Eg. If you're re-using a component that
 * adds dependencies but you don't want that component or its dependencies
 * as your own dependency
 */
export const OrphanedTraceContext = ({children}: {children: ReactNode}) => {
  return (
    <TraceContext.Provider
      value={useMemo(
        () => ({
          createDependency: () => null,
          addDependency: () => {},
          cancelDependency: () => {},
          completeDependency: () => {},
          completeDependencyWithError: () => {},
        }),
        [],
      )}
    >
      {children}
    </TraceContext.Provider>
  );
};

export class Dependency {
  public readonly name: string;

  constructor(name: string) {
    this.name = name;
  }
}

/** Use this to declare a dependency on an apollo query result */
export function useQueryResultDependency(queryResult: QueryResult<any>, name: string) {
  const dep = useDependency(name);
  const hasData = !!queryResult.data;
  const hasError = !!queryResult.error;

  useLayoutEffect(() => {
    if (hasData) {
      dep.completeDependency();
    }
  }, [dep, hasData]);

  useLayoutEffect(() => {
    if (!hasData && hasError) {
      dep.completeDependencyWithError();
    }
  }, [dep, hasData, hasError]);
}

export function useDependency(name: string) {
  const {
    addDependency,
    cancelDependency,
    completeDependency,
    completeDependencyWithError,
    createDependency,
  } = useContext(TraceContext);

  const dependency = useMemo(() => createDependency(name), [createDependency, name]);

  useLayoutEffect(() => {
    addDependency(dependency);
    return () => {
      // By default cancel a dependency when the component unmounts.
      // Rely on the user of TraceContext to track if the dependency
      // was already completed prior to this.
      cancelDependency(dependency);
    };
  }, [addDependency, cancelDependency, dependency]);

  return useMemo(
    () => ({
      completeDependency: () => {
        completeDependency(dependency);
      },
      cancelDependency: () => {
        cancelDependency(dependency);
      },
      completeDependencyWithError: () => {
        completeDependencyWithError(dependency);
      },
    }),
    [cancelDependency, completeDependency, completeDependencyWithError, dependency],
  );
}
