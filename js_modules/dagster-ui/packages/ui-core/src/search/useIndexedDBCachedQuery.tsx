import {ApolloQueryResult, DocumentNode, OperationVariables, useApolloClient} from '@apollo/client';
import {cache} from 'idb-lru-cache';
import React from 'react';

type CacheData<TQuery> = {
  data: TQuery;
  version: number;
};

let fetchState: Record<
  string,
  {
    onFetched: ((value: any) => void)[];
  }
> = {};

/**
 * Returns data from the indexedDB cache initially while loading is true.
 * Fetches data from the network/cache initially and does not receive any updates afterwards
 * Uses fetch-policy: no-cache to avoid slow apollo cache normalization
 */
export function useIndexedDBCachedQuery<TQuery, TVariables extends OperationVariables>({
  key,
  query,
  version,
  variables,
}: {
  key: string;
  query: DocumentNode;
  version: number;
  variables?: TVariables;
}) {
  const client = useApolloClient();

  const lru = React.useMemo(
    () => cache<string, CacheData<TQuery>>({dbName: `indexdbQueryCache:${key}`, maxCount: 1}),
    [key],
  );

  const [data, setData] = React.useState<TQuery | null>(null);

  const [loading, setLoading] = React.useState(false);
  const [cacheBreaker, setCacheBreaker] = React.useState(0);

  React.useEffect(() => {
    (async () => {
      if (await lru.has('cache')) {
        const {value} = await lru.get('cache');
        if (value) {
          if (version === (value.version || null)) {
            setData(value.data);
          }
        }
      }
    })();
  }, [lru, version, cacheBreaker]);

  const fetch = React.useCallback(async () => {
    if (window.__LOG) {
      debugger;
    }
    window.__LOG && console.log('fetch', key, fetchState);

    setLoading(true);
    if (fetchState[key]) {
      console.log('subscribing');
      return await new Promise<ApolloQueryResult<TQuery>>((res) => {
        fetchState[key]?.onFetched.push((value) => {
          setCacheBreaker((v) => v + 1);
          res(value);
        });
      });
    }
    fetchState[key] = {onFetched: []};
    // Use client.query here so that we initially use the apollo cache if any data is available in it
    // and so that we don't subscribe to any updates to that cache (useLazyQuery and useQuery would both subscribe to updates to the
    // cache which can be very slow)
    const queryResult = await client.query<TQuery, TVariables>({
      query,
      variables,
      fetchPolicy: 'no-cache', // Don't store the result in the cache,
      // should help avoid page stuttering due to granular updates to the data
    });
    const {data} = queryResult;
    if (window.__LOG) {
      console.log(data.workspaceOrError.locationEntries.length);
    }
    setLoading(false);
    lru.set(
      'cache',
      {data, version},
      {
        expiry: new Date('3000'), // never expire,
      },
    );
    delete fetchState[key];
    const onFetched = fetchState[key]?.onFetched;
    window.__LOG && console.log('setting data');
    setData(data);
    window.__LOG && console.log('onfetched');
    onFetched?.forEach((cb) => cb(queryResult));
    window.__LOG && console.log('returning');
    return queryResult;
  }, [client, key, lru, query, variables, version]);

  return {
    fetch,
    data,
    loading,
  };
}

export const __resetForJest = () => {
  fetchState = {};
};
