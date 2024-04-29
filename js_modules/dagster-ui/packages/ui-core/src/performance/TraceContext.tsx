import {QueryResult} from '@apollo/client';
import {ReactNode, createContext, useContext, useLayoutEffect, useMemo} from 'react';

export type DependencyProps = {
  name: string;
};
type TraceContextType = {
  createDependency: (_props: DependencyProps) => Dependency | null;
  addDependency: (_dep: Dependency | null) => void;
  cancelDependency: (_dep: Dependency | null) => void;
  completeDependency: (_dep: Dependency | null) => void;
};

export const TraceContext = createContext<TraceContextType>({
  createDependency: (_props) => null,
  addDependency: (_dep) => {},
  cancelDependency: (_dep) => {},
  completeDependency: (_dep) => {},
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

  constructor(props: DependencyProps) {
    this.name = props.name;
  }
}

/** Use this to declare a dependency on an apollo query result */
export function useQueryResultDependency(queryResult: QueryResult<any>, name: string) {
  const dep = useDependency(useMemo(() => ({name}), [name]));
  const hasData = !!queryResult.data;

  useLayoutEffect(() => {
    if (hasData) {
      dep.completeDependency();
    }
  }, [dep, hasData]);
}

export function useDependency(props: DependencyProps) {
  const {addDependency, cancelDependency, completeDependency, createDependency} =
    useContext(TraceContext);

  const dependency = useMemo(() => createDependency(props), [createDependency, props]);

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
    }),
    [cancelDependency, completeDependency, dependency],
  );
}
