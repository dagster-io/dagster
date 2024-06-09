import {useQuery} from '@apollo/client';
import {DocumentNode} from 'graphql';
import {useEffect, useState} from 'react';

import {useQueryRefreshAtInterval} from '../app/QueryRefresh';

type FetchState = {
  hasMore: boolean;
  cursor: string | null | undefined;
};

export function useCursorAccumulatedQuery<T, TVars extends {cursor?: string | null}, U>(options: {
  query: DocumentNode;
  skip?: boolean;
  variables: Omit<TVars, 'cursor'>;
  getResultArray: (result: T | undefined) => U[];
  getNextFetchState: (result: T | undefined) => FetchState | null;
}) {
  const [fetched, setFetched] = useState<U[] | null>(null);
  const [fetchState, setFetchState] = useState<FetchState>({hasMore: true, cursor: undefined});
  const {query, skip, variables, getResultArray, getNextFetchState} = options;

  const queryResult = useQuery<T, TVars>(query, {
    variables: {...variables, cursor: fetchState.cursor} as TVars,
    notifyOnNetworkStatusChange: true,
    skip,
  });

  useEffect(() => {
    if (!queryResult.data) {
      return;
    }
    const result = getResultArray(queryResult.data);
    setFetched((fetched) => (fetched || []).concat(result));
    const next = getNextFetchState(queryResult.data);
    if (next) {
      setFetchState(next);
    }
  }, [queryResult, getResultArray, getNextFetchState]);

  // When we have reached the last event, switch to refreshing every 5s
  const refreshState = useQueryRefreshAtInterval(queryResult, 5 * 1000, !fetchState.hasMore);

  return {fetched, refreshState};
}
