import {useApolloClient} from '@apollo/client';
import {DocumentNode} from 'graphql';
import {useEffect, useRef, useState} from 'react';
import {EventEmitter} from 'ws';

import {useRefreshAtInterval} from '../app/QueryRefresh';

type FetchState = {
  hasMore: boolean;
  cursor: string | null | undefined;
};

type FetcherFunction<DataType, CursorType, ErrorType> = (
  cursor: CursorType | undefined,
) => Promise<{
  data: DataType[];
  hasMore: boolean;
  cursor: CursorType | undefined;
  error: ErrorType;
}>;

class PaginatingDataFetcher<DataType, CursorType, ErrorType> extends EventEmitter {
  private hasMoreData = true;
  private dataSoFar: DataType[] = [];
  private currentCursor: CursorType | undefined = undefined;
  private stopped: boolean = false;
  private fetchData: FetcherFunction<DataType, CursorType, ErrorType>;

  constructor(fetchData: FetcherFunction<DataType, CursorType, ErrorType>) {
    super();
    this.fetchData = fetchData;
  }

  async start() {
    if (this.stopped) {
      throw new Error('PaginatingDataFetcher cannot be restarted');
    }
    this.emit('status-change', true);

    while (this.hasMoreData) {
      const {cursor, hasMore, data, error} = await this.fetchData(this.currentCursor);
      if (error) {
        this.emit('status-change', false);
        throw error;
      }
      if (this.stopped) {
        break;
      }
      this.currentCursor = cursor;
      this.hasMoreData = hasMore;
      if (data.length > 0) {
        this.dataSoFar = this.dataSoFar.concat(data);
        this.emit('data', this.dataSoFar);
      }
    }
    this.emit('status-change', false);
  }

  stop() {
    this.stopped = true;
  }
}

export function useCursorAccumulatedQuery<T, TVars extends {cursor?: string | null}, U>({
  query,
  variables,
  getResultArray,
  getNextFetchState,
}: {
  query: DocumentNode;
  variables: Omit<TVars, 'cursor'>;
  getResultArray: (result: T | undefined) => U[];
  getNextFetchState: (result: T | undefined) => FetchState | null;
}) {
  const [fetched, setFetched] = useState<U[] | null>(null);
  const [fetching, setFetching] = useState(false);
  const client = useApolloClient();

  const refresh = useRef<() => Promise<void>>(() => Promise.resolve());
  const refreshState = useRefreshAtInterval({
    refresh: refresh.current,
    enabled: !fetching,
    intervalMs: 10000,
  });

  useEffect(() => {
    const fetcher = new PaginatingDataFetcher(async (cursor: string | undefined) => {
      const resp = await client.query<T, TVars>({
        variables: {...variables, cursor},
        query,
      });

      // Todo align this with the data fetcher better
      return {...getNextFetchState(resp.data), data: getResultArray(resp.data), error: null};
    });

    refresh.current = () => fetcher.start();
    fetcher.on('data', setFetched);
    fetcher.on('status-change', setFetching);
    fetcher.on('finish', () => setFetching(false));
    void fetcher.start();
    return () => {
      fetcher.removeAllListeners('data');
      fetcher.removeAllListeners('status-change');
      fetcher.removeAllListeners('finish');
      fetcher.stop();
    };
  }, [query, client, variables, getResultArray, getNextFetchState]);

  return {fetched, refreshState};
}
