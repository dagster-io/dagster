import {ApolloClient, DocumentNode, OperationVariables, useApolloClient} from '@apollo/client';
import {cache} from 'idb-lru-cache';
import memoize from 'lodash/memoize';
import React, {createContext, useCallback, useContext} from 'react';

type CacheData<TQuery> = {
  data: TQuery;
  version: number;
};

export const KEY_PREFIX = 'indexdbQueryCache:';

export class CacheManager<TQuery> {
  private cache: ReturnType<typeof cache<string, CacheData<TQuery>>>;
  private key: string;

  constructor(key: string) {
    this.key = `${KEY_PREFIX}${key}`;
    this.cache = cache<string, CacheData<TQuery>>({dbName: this.key, maxCount: 1});
  }

  async get(version: number): Promise<TQuery | null> {
    if (await this.cache.has('cache')) {
      const {value} = await this.cache.get('cache');
      if (value && version === value.version) {
        return value.data;
      }
    }
    return null;
  }

  set(data: TQuery, version: number): Promise<void> {
    return this.cache.set('cache', {data, version}, {expiry: new Date('3030-01-01')});
  }
}

interface QueryHookParams<TVariables extends OperationVariables, TQuery> {
  key: string;
  query: DocumentNode;
  version: number;
  variables?: TVariables;
  onCompleted?: (data: TQuery) => void;
}

export function useIndexedDBCachedQuery<TQuery, TVariables extends OperationVariables>({
  key,
  query,
  version,
  variables,
}: QueryHookParams<TVariables, TQuery>) {
  const client = useApolloClient();
  const [data, setData] = React.useState<TQuery | null>(null);
  const [loading, setLoading] = React.useState(true);

  const getData = useGetData();

  const fetch = useCallback(
    async (bypassCache = false) => {
      setLoading(true);
      const newData = await getData<TQuery, TVariables>({
        client,
        key,
        query,
        variables,
        version,
        bypassCache,
      });
      setData(newData);
      setLoading(false);
    },
    [getData, client, key, query, variables, version],
  );

  React.useEffect(() => {
    fetch();
  }, [fetch]);

  return {
    data,
    loading,
    fetch: useCallback(() => fetch(true), [fetch]),
  };
}

interface FetchParams<TVariables extends OperationVariables> {
  client: ApolloClient<any>;
  key: string;
  query: DocumentNode;
  variables?: TVariables;
  version: number;
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
    }: FetchParams<TVariables>): Promise<TQuery> => {
      const cacheManager = getCacheManager<TQuery>(key);

      if (!bypassCache) {
        const cachedData = await cacheManager.get(version);
        if (cachedData !== null) {
          return cachedData;
        }
      }

      const currentState = fetchState[key];
      // Handle concurrent fetch requests
      if (currentState) {
        return new Promise((resolve) => {
          currentState!.onFetched.push(resolve as any);
        });
      }

      const state = {onFetched: [] as ((value: any) => void)[]};
      fetchState[key] = state;

      const queryResult = await client.query<TQuery, TVariables>({
        query,
        variables,
        fetchPolicy: 'no-cache',
      });

      const {data} = queryResult;
      await cacheManager.set(data, version);

      const onFetchedHandlers = state.onFetched;
      if (fetchState[key] === state) {
        delete fetchState[key]; // Clean up fetch state after handling
      }

      onFetchedHandlers.forEach((handler) => handler(data)); // Notify all waiting fetches

      return data;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
}

export function useGetCachedData() {
  const {getCacheManager} = useContext(IndexedDBCacheContext);

  return useCallback(
    async <TQuery,>({key, version}: {key: string; version: number}) => {
      const cacheManager = getCacheManager<TQuery>(key);
      return await cacheManager.get(version);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
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
