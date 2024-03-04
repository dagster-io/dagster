import {DocumentNode, OperationVariables, useApolloClient} from '@apollo/client';
import {cache} from 'idb-lru-cache';
import React from 'react';

const ONE_WEEK = 1000 * 60 * 60 * 24 * 7;

/**
 * Returns data from the indexedDB cache initially while loading is true.
 * Fetches data from the network/cache initially and does not receive any updates afterwards
 */
export function useIndexedDBCachedQuery<TQuery, TVariables extends OperationVariables>({
  key,
  query,
  variables,
}: {
  key: string;
  query: DocumentNode;
  variables: TVariables;
}) {
  const client = useApolloClient();

  const lru = React.useMemo(
    () => cache<string, TQuery>({dbName: `indexdbQueryCache:${key}`, maxCount: 1}),
    [key],
  );

  const [data, setData] = React.useState<TQuery | null>(null);

  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    (async () => {
      const {value} = await lru.get('cache');
      if (value) {
        setData(value);
      }
    })();
  }, [lru]);

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
    lru.set('cache', data, {
      expiry: new Date(Date.now() + ONE_WEEK),
    });
    setData(data);
  }, [client, lru, query, variables]);

  return {
    fetch,
    data,
    loading,
  };
}
