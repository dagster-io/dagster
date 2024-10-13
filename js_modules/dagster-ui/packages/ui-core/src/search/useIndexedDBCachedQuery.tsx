import {cache} from 'idb-lru-cache';
import memoize from 'lodash/memoize';
import React, {createContext, useCallback, useContext, useEffect} from 'react';

import {
  ApolloClient,
  ApolloError,
  DocumentNode,
  OperationVariables,
  useApolloClient,
} from '../apollo-client';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {CompletionType, useBlockTraceUntilTrue} from '../performance/TraceContext';

type CacheData<TQuery> = {
  data: TQuery;
  version: number | string;
};

export const KEY_PREFIX = 'indexdbQueryCache:';

export class CacheManager<TQuery> {
  private cache: ReturnType<typeof cache<string, CacheData<TQuery>>> | undefined;
  private key: string;
  private current?: CacheData<TQuery>;
  private currentAwaitable?: Promise<TQuery | undefined>;

  constructor(key: string) {
    this.key = `${KEY_PREFIX}${key}`;
    try {
      this.cache = cache<string, CacheData<TQuery>>({dbName: this.key, maxCount: 1});
    } catch (e) {}
  }

  async get(version: number | string): Promise<TQuery | undefined> {
    if (this.current) {
      return this.current.data;
    }
    if (!this.currentAwaitable) {
      this.currentAwaitable = new Promise(async (res) => {
        if (!this.cache) {
          res(undefined);
          return;
        }
        if (await this.cache.has('cache')) {
          const {value} = await this.cache.get('cache');
          if (value && version === value.version) {
            this.current = value;
            res(value.data);
          } else {
            res(undefined);
          }
        } else {
          res(undefined);
        }
      });
    }
    return await this.currentAwaitable;
  }

  async set(data: TQuery, version: number | string): Promise<void> {
    if (
      this.current?.data === data ||
      (JSON.stringify(this.current?.data) === JSON.stringify(data) &&
        this.current?.version === version)
    ) {
      return;
    }
    if (!this.cache) {
      return;
    }
    return this.cache.set('cache', {data, version}, {expiry: new Date('3030-01-01')});
  }

  async clear() {
    if (!this.cache) {
      return;
    }
    await this.cache.delete('cache');
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

  const getData = useGetData();
  const getCachedData = useGetCachedData();

  const fetch = useCallback(
    async (bypassCache = false) => {
      setLoading(true);
      const {data, error} = await getData<TQuery, TVariables>({
        client,
        key,
        query,
        variables,
        version,
        bypassCache,
      });
      if (
        data &&
        // Work around a weird jest issue where it returns an empty object if no mocks are found...
        Object.keys(data).length &&
        (!dataRef.current || JSON.stringify(dataRef.current) !== JSON.stringify(data))
      ) {
        setData(data);
      }
      setError(error);
      setLoading(false);
    },
    // exclude variables, instead JSON stringify it to avoid changing this reference if the caller hasn't memoized it
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [getData, client, key, query, JSON.stringify(variables), version, dataRef],
  );

  React.useEffect(() => {
    if (skip) {
      return;
    }
    getCachedData<TQuery>({key, version}).then((data) => {
      if (data && !dataRef.current) {
        setData(data);
        setLoading(false);
      }
    });
  }, [key, version, getCachedData, dataRef, skip]);

  React.useEffect(() => {
    if (skip) {
      return;
    }
    fetch(true);
  }, [fetch, skip]);

  const dep = useBlockTraceUntilTrue(`useIndexedDBCachedQuery-${key}`, !!data, {
    skip,
  });
  useEffect(() => {
    if (error) {
      dep.completeDependency(CompletionType.ERROR);
    }
  }, [error, dep]);

  return {
    data,
    called: true, // Add called for compatibility with useBlockTraceOnQueryResult
    error,
    loading,
    fetch: useCallback(() => fetch(true), [fetch]),
  };
}

interface FetchParams<TVariables extends OperationVariables> {
  client: ApolloClient<any>;
  key: string;
  query: DocumentNode;
  variables?: TVariables;
  version: number | string;
  bypassCache?: boolean;
}

export function useGetData() {
  const {getCacheManager, fetchState} = useContext(IndexedDBCacheContext);

  return useCallback(
    async <TQuery, TVariables extends OperationVariables>({
      client,
      key,
      query,
      variables,
      version,
      bypassCache = false,
    }: FetchParams<TVariables>): Promise<{data: TQuery; error: ApolloError | undefined}> => {
      const cacheManager = getCacheManager<TQuery>(key);

      if (!bypassCache) {
        const cachedData = await cacheManager.get(version);
        if (cachedData !== undefined) {
          return {data: cachedData, error: undefined};
        }
      }

      const currentState = fetchState[key];
      // Handle concurrent fetch requests
      if (currentState) {
        return new Promise((resolve) => {
          currentState!.onFetched.push(resolve as any);
        });
      }

      const state = {
        onFetched: [] as ((value: Pick<typeof queryResult, 'data' | 'error'>) => void)[],
      };
      fetchState[key] = state;

      const queryResult = await client.query<TQuery, TVariables>({
        query,
        variables,
        fetchPolicy: 'no-cache',
      });

      const {data, error} = queryResult;

      if (data && !error) {
        await cacheManager.set(data, version);
      }

      const onFetchedHandlers = state.onFetched;
      if (fetchState[key] === state) {
        delete fetchState[key]; // Clean up fetch state after handling
      }

      onFetchedHandlers.forEach((handler) => handler({data, error})); // Notify all waiting fetches

      return {data, error};
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
}

export function useGetCachedData() {
  const {getCacheManager} = useContext(IndexedDBCacheContext);

  return useCallback(
    async <TQuery,>({key, version}: {key: string; version: number | string}) => {
      const cacheManager = getCacheManager<TQuery>(key);
      return await cacheManager.get(version);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
}
export function useClearCachedData() {
  const {getCacheManager} = useContext(IndexedDBCacheContext);
  return useCallback(
    async <TQuery,>({key}: {key: string}) => {
      const cacheManager = getCacheManager<TQuery>(key);
      await cacheManager.clear();
    },
    [getCacheManager],
  );
}

const contextValue = createIndexedDBCacheContextValue();
export const IndexedDBCacheContext = createContext(contextValue);

export function createIndexedDBCacheContextValue() {
  return {
    getCacheManager: memoize(<TQuery,>(key: string) => {
      return new CacheManager<TQuery>(key);
    }),
    fetchState: {} as Record<
      string,
      {
        onFetched: ((value: any) => void)[];
      }
    >,
  };
}

export const __resetForJest = () => {
  Object.assign(contextValue, createIndexedDBCacheContextValue());
};
