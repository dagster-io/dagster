import {ReactNode, createContext, useContext, useLayoutEffect, useMemo} from 'react';

import {QueryResult} from '../apollo-client';
import {useDangerousRenderEffect} from '../hooks/useDangerousRenderEffect';

export enum CompletionType {
  SUCCESS = 1,
  ERROR = 2,
  CANCELLED = 3,
}

type TraceContextType = {
  createDependency: (_name: string) => Dependency | null;
  addDependency: (_dep: Dependency | null) => void;
  completeDependency: (_dep: Dependency | null, type: CompletionType) => void;
};

export const TraceContext = createContext<TraceContextType>({
  createDependency: (_name: string) => null,
  addDependency: (_dep) => {},
  completeDependency: (_dep, _type) => {},
});

/**
 * Use this to wrap child react components who should not count
 * toward display done. Eg. If you're re-using a component that
 * adds dependencies but you don't want that component or its dependencies
 * as your own dependency
 */
export const OrphanDependenciesTraceContext = ({children}: {children: ReactNode}) => {
  return (
    <TraceContext.Provider
      value={useMemo(
        () => ({
          createDependency: () => null,
          addDependency: () => {},
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

  constructor(name: string) {
    this.name = name;
  }
}

type Options = {
  uid?: string;
  skip?: boolean;
};

/** Use this to declare a dependency on an apollo query result */
export function useBlockTraceOnQueryResult(
  queryResult: Pick<QueryResult<any, any>, 'data' | 'error' | 'called'>,
  name: string,
  opts: Options = {},
) {
  const dep = useTraceDependency(name, {skip: opts.skip || !queryResult.called});
  const hasData = !!queryResult.data;
  const hasError = !!queryResult.error;

  useDangerousRenderEffect(() => {
    if (hasData && !hasError) {
      dep.completeDependency(CompletionType.SUCCESS);
    }
  }, [dep, hasData, hasError]);

  useDangerousRenderEffect(() => {
    if (!hasData && hasError) {
      dep.completeDependency(CompletionType.ERROR);
    }
  }, [dep, hasData, hasError]);
}

export function useTraceDependency(name: string, opts: Options = {}) {
  const {addDependency, completeDependency, createDependency} = useContext(TraceContext);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const dependency = useMemo(() => createDependency(name), [createDependency, name, opts?.uid]);

  useDangerousRenderEffect(() => {
    if (!opts?.skip) {
      addDependency(dependency);
    }
  }, [dependency, opts.skip]);

  useLayoutEffect(() => {
    return () => {
      // By default cancel a dependency when the component unmounts.
      // Rely on the user of TraceContext to track if the dependency
      // was already completed prior to this.
      completeDependency(dependency, CompletionType.CANCELLED);
    };
  }, [addDependency, completeDependency, dependency]);

  return useMemo(
    () => ({
      completeDependency: (type: CompletionType) => {
        completeDependency(dependency, type);
      },
    }),
    [completeDependency, dependency],
  );
}

export function useBlockTraceUntilTrue(name: string, isSuccessful: boolean, opts: Options = {}) {
  const dep = useTraceDependency(name, opts);
  useLayoutEffect(() => {
    if (isSuccessful) {
      dep.completeDependency(CompletionType.SUCCESS);
    }
  }, [dep, isSuccessful, name]);
  return dep;
}
