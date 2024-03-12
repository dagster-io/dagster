import {DocumentNode, OperationVariables, useApolloClient} from '@apollo/client';
import {cache} from 'idb-lru-cache';
import React from 'react';

const ONE_WEEK = 1000 * 60 * 60 * 24 * 7;

type CacheData<TQuery> = {
  data: TQuery;
  version: number;
};

/**
 * Returns data from the indexedDB cache initially while loading is true.
 * Fetches data from the network/cache initially and does not receive any updates afterwards
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
  }, [lru, version]);

  const didFetch = React.useRef(false);

  const fetch = React.useCallback(async () => {
    if (didFetch.current) {
      return;
    }
    didFetch.current = true;
    setLoading(true);
    // Use client.query here so that we initially use the apollo cache if any data is available in it
    // and so that we don't subscribe to any updates to that cache (useLazyQuery and useQuery would both subscribe to updates to the
    // cache which can be very slow)
    const {data} = await client.query<TQuery, TVariables>({
      query,
      variables,
    });
    setLoading(false);
    lru.set(
      'cache',
      {data, version},
      {
        expiry: new Date(Date.now() + ONE_WEEK),
      },
    );
    setData(data);
  }, [client, lru, query, variables, version]);

  return {
    fetch,
    data,
    loading,
  };
}
