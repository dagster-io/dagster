import React, {useCallback, useEffect, useMemo} from 'react';

import {
  ApolloClient,
  ApolloError,
  DocumentNode,
  OperationVariables,
  useApolloClient,
} from '../apollo-client';
import {usePreviousDistinctValue} from '../hooks/usePrevious';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {CompletionType, useBlockTraceUntilTrue} from '../performance/TraceContext';
import {cache} from '../util/idb-lru-cache';
import {weakMapMemoize} from '../util/weakMapMemoize';

export type CacheData<TQuery> = {
  data: TQuery;
  version: number | string;
};

export const KEY_PREFIX = 'indexdbQueryCache:';

class CacheManager<TQuery> {
  private cache: ReturnType<typeof cache<CacheData<TQuery>>> | undefined;
  private key: string;
  // In-memory mirror of the single entry we keep in IndexedDB. It must be kept in sync with
  // whatever we last read from or wrote to IndexedDB, otherwise reads can serve data that has
  // already been replaced or deleted on disk.
  private current?: CacheData<TQuery>;
  private currentAwaitable?: Promise<void>;

  constructor(key: string) {
    this.key = `${KEY_PREFIX}${key}`;
    try {
      this.cache = cache<CacheData<TQuery>>({dbName: this.key, maxCount: 1});
    } catch {}
  }

  async get(version: number | string): Promise<TQuery | undefined> {
    if (!this.current) {
      if (!this.currentAwaitable) {
        this.currentAwaitable = this.readFromCache();
      }
      await this.currentAwaitable;
    }
    const current = this.current;
    // The version is checked on every read, not just on the read that populated `current`, so a
    // caller asking for a different version never receives the entry cached for another one.
    if (current && current.version === version) {
      return current.data;
    }
    return undefined;
  }

  private async readFromCache(): Promise<void> {
    if (!this.cache) {
      return;
    }
    try {
      if (!(await this.cache.has('cache'))) {
        return;
      }
      const value = (await this.cache.get('cache'))?.value;
      // A `set` or `clear` may have landed while this read was in flight; that value is newer
      // than what we just read off disk, so don't clobber it.
      if (value && !this.current) {
        this.current = value;
      }
    } catch {}
  }

  async set(data: TQuery, version: number | string): Promise<void> {
    if (
      this.current?.version === version &&
      (this.current.data === data || stringified(this.current.data) === stringified(data))
    ) {
      return;
    }
    if (!this.cache) {
      return;
    }
    const entry = {data, version};
    // Keep the in-memory mirror in sync with what we just persisted, so a subsequent read
    // doesn't serve the value this one replaced.
    this.current = entry;
    // Reads no longer need to consult IndexedDB: `current` now holds the newest value.
    this.currentAwaitable = Promise.resolve();
    return this.cache.set('cache', entry);
  }

  async clear() {
    this.current = undefined;
    // Resolve immediately rather than re-reading the entry we're about to delete.
    this.currentAwaitable = Promise.resolve();
    if (!this.cache) {
      return;
    }
    await this.cache.delete('cache');
  }
}

const globalFetchStates: Record<string, {onFetched: ((value: any) => void)[]}> = {};

export class IndexedDBQueryCache<TQuery, TVariables extends OperationVariables> {
  private cacheManager: CacheManager<TQuery>;
  private key: string;
  private version: number | string;
  private queryFn: (variables?: TVariables) => Promise<{data: TQuery | undefined; error: any}>;
  private variables?: TVariables;
  private queryId: number;

  constructor({
    key,
    version,
    variables,
    queryFn,
  }: {
    key: string;
    version: number | string;
    variables?: TVariables;
    queryFn: (variables?: TVariables) => Promise<{data: TQuery | undefined; error: any}>;
  }) {
    this.key = key;
    this.queryId = 0;
    this.version = version;
    this.variables = variables;
    this.queryFn = queryFn;
    this.cacheManager = getCacheManager(key);

    // Try to get cached data immediately (but don't await it in constructor)
    this.getCachedData();
  }

  async getCachedData(): Promise<TQuery | undefined> {
    return await this.cacheManager.get(this.version);
  }

  async fetchData(
    bypassCache = false,
  ): Promise<{data: TQuery | undefined; error: ApolloError | undefined}> {
    if (!bypassCache) {
      const cachedData = await this.getCachedData();
      if (cachedData !== undefined) {
        return {data: cachedData, error: undefined};
      }
    }
    const globalKey = `${this.key}-${JSON.stringify(this.variables)}-${this.version}`;

    const currentState = globalFetchStates[globalKey];
    if (currentState) {
      return new Promise((resolve) => {
        currentState.onFetched.push(resolve);
      });
    }

    const state = {
      onFetched: [] as ((value: {
        data: TQuery | undefined;
        error: ApolloError | undefined;
      }) => void)[],
    };
    globalFetchStates[globalKey] = state;

    const result = await this.queryFn(this.variables);

    if (result.data && !result.error) {
      const dataToCache = result.data;
      setTimeout(() => {
        // Let the UI render before setting the cache since it could be slow
        this.cacheManager.set(dataToCache, this.version);
      }, 1);
    }

    const onFetchedHandlers = state.onFetched;
    if (globalFetchStates[globalKey] === state) {
      delete globalFetchStates[globalKey]; // Clean up fetch state after handling
    }

    onFetchedHandlers.forEach((handler) => {
      try {
        handler(result);
      } catch (e) {
        console.error('Error in onFetched handler', e);
      }
    }); // Notify all waiting fetches

    return result;
  }

  async clearCache(): Promise<void> {
    await this.cacheManager.clear();
  }

  updateVariables(variables: TVariables): void {
    this.variables = variables;
    this.queryId++;
  }

  updateVersion(version: number | string): void {
    this.version = version;
    this.queryId++;
  }
}

export class ApolloIndexedDBQueryCache<
  TQuery,
  TVariables extends OperationVariables,
> extends IndexedDBQueryCache<TQuery, TVariables> {
  constructor({
    client,
    key,
    query,
    version,
    variables,
  }: {
    client: ApolloClient<any>;
    key: string;
    query: DocumentNode;
    version: number | string;
    variables?: TVariables;
  }) {
    const queryFn = async (vars?: TVariables) => {
      try {
        const queryResult = await client.query<TQuery, TVariables>({
          query,
          variables: vars,
          fetchPolicy: 'no-cache',
        });
        return {data: queryResult.data, error: queryResult.error};
      } catch (error) {
        return {data: undefined, error};
      }
    };

    super({key, version, variables, queryFn});
  }
}

interface QueryHookParams<TVariables extends OperationVariables, TQuery> {
  key: string;
  query: DocumentNode;
  version: number | string;
  variables?: TVariables;
  onCompleted?: (data: TQuery) => void;
}

export function useIndexedDBCachedQuery<TQuery, TVariables extends OperationVariables>({
  key,
  skip,
  query,
  version,
  variables,
}: QueryHookParams<TVariables, TQuery> & {skip?: boolean}) {
  const client = useApolloClient();
  const [data, setData] = React.useState<TQuery | undefined>(undefined);
  const [error, setError] = React.useState<ApolloError | undefined>(undefined);
  const [loading, setLoading] = React.useState(true);
  const dataRef = useUpdatingRef(data);

  const cacheRef = useMemo(() => {
    return new ApolloIndexedDBQueryCache<TQuery, TVariables>({
      client,
      key,
      query,
      version,
      variables,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, query, client]);

  const fetch = useCallback(
    async (bypassCache = false) => {
      setLoading(true);
      const {data, error} = await cacheRef.fetchData(bypassCache);

      if (
        data &&
        // Work around a weird jest issue where it returns an empty object if no mocks are found...
        Object.keys(data).length &&
        (!dataRef.current || stringified(dataRef.current) !== stringified(data))
      ) {
        setData(data);
      }
      setError(error);
      setLoading(false);
    },
    [dataRef, cacheRef],
  );

  React.useEffect(() => {
    if (skip) {
      return;
    }

    cacheRef.getCachedData().then((data) => {
      if (data && !dataRef.current) {
        setData(data);
        setLoading(false);
      }
    });
  }, [dataRef, skip, cacheRef]);

  // JSON stringify variables to avoid refetching if the caller hasn't memoized it
  const stringifiedVariables = useMemo(() => JSON.stringify(variables ?? {}), [variables]);

  React.useEffect(() => {
    if (skip) {
      return;
    }
    cacheRef.updateVariables(JSON.parse(stringifiedVariables));
    cacheRef.updateVersion(version);
    fetch(true);
  }, [fetch, skip, version, cacheRef, stringifiedVariables]);

  const dep = useBlockTraceUntilTrue(`useIndexedDBCachedQuery-${key}`, !!data, {
    skip,
  });
  useEffect(() => {
    if (error) {
      dep.completeDependency(CompletionType.ERROR);
    }
  }, [error, dep]);

  const previousData = usePreviousDistinctValue(data);

  return {
    data,
    previousData,
    called: true, // Add called for compatibility with useBlockTraceOnQueryResult
    error,
    loading,
    fetch: useCallback(() => fetch(true), [fetch]),
  };
}

export function useGetData() {
  const apolloClient = useApolloClient();

  return useCallback(
    async <TData, TVariables extends OperationVariables>({
      client,
      query,
      key,
      version,
      variables,
      bypassCache = false,
    }: {
      client?: ApolloClient<any>;
      query: DocumentNode;
      key: string;
      version: number | string;
      variables?: TVariables;
      bypassCache?: boolean;
    }) => {
      const clientToUse = client || apolloClient;

      // Create a cache instance or reuse an existing one
      const queryCache = new ApolloIndexedDBQueryCache<TData, TVariables>({
        client: clientToUse,
        key,
        query,
        version,
        variables,
      });

      const result = await queryCache.fetchData(bypassCache);

      return {
        data: result.data,
        error: result.error,
      };
    },
    [apolloClient],
  );
}

export async function getCachedData<TQuery>({
  key,
  version,
}: {
  key: string;
  version: number | string;
}) {
  return await getCacheManager<TQuery>(key).get(version);
}

export async function setCachedData<TQuery>({
  key,
  version,
  data,
}: {
  key: string;
  version: number | string;
  data: TQuery;
}) {
  await getCacheManager<TQuery>(key).set(data, version);
}

export async function clearCachedData<TQuery>({key}: {key: string}) {
  await getCacheManager<TQuery>(key).clear();
}

export let getCacheManager = weakMapMemoize(<TQuery,>(key: string) => {
  return new CacheManager<TQuery>(key);
});

export const __resetForJest = () => {
  Object.keys(globalFetchStates).forEach((key) => delete globalFetchStates[key]);
  getCacheManager = weakMapMemoize(<TQuery,>(key: string) => {
    return new CacheManager<TQuery>(key);
  });
};

const stringified = weakMapMemoize((data: any) => {
  try {
    return JSON.stringify(data);
  } catch {
    return '';
  }
});
