import {OperationVariables, useApolloClient} from '@apollo/client';
import {DocumentNode} from 'graphql';
import {useEffect, useMemo, useState} from 'react';

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

class PaginatingDataFetcher<DataType, CursorType, ErrorType> {
  private hasMoreData = true;
  private dataSoFar: DataType[] = [];
  private currentCursor: CursorType | undefined = undefined;
  private fetchPromise?: Promise<void>;
  private fetchData: FetcherFunction<DataType, CursorType, ErrorType>;
  private stopped: boolean = false;
  private onData: (data: DataType[]) => void;
  private onError?: (error: ErrorType) => void;

  constructor({
    fetchData,
    onData,
    onError,
  }: {
    fetchData: FetcherFunction<DataType, CursorType, ErrorType>;
    onData: (data: DataType[]) => void;
    onError?: (error: ErrorType) => void;
  }) {
    this.fetchData = fetchData;
    this.onData = onData;
    this.onError = onError;
  }

  async fetch() {
    if (this.fetchPromise) {
      return await this.fetchPromise;
    }
    this.fetchPromise = new Promise(async (res) => {
      while (this.hasMoreData && !this.stopped) {
        const {cursor, hasMore, data, error} = await this.fetchData(this.currentCursor);
        if (error) {
          this.onError?.(error);
          break;
        }
        if (this.stopped) {
          break;
        }
        this.currentCursor = cursor;
        this.hasMoreData = hasMore;
        if (data.length > 0) {
          this.dataSoFar = this.dataSoFar.concat(data);
          this.onData(this.dataSoFar);
        }
      }
      res();
    });
    const result = await this.fetchPromise!;
    this.fetchPromise = undefined;
    return result;
  }

  stop() {
    this.stopped = true;
  }
}

export function useCursorAccumulatedQuery<
  TQuery,
  TVars extends OperationVariables & {cursor?: string | null},
  U,
>({
  query,
  variables,
  getResultArray,
  getNextFetchState,
}: {
  query: DocumentNode;
  variables: Omit<TVars, 'cursor'>;
  getResultArray: (result: TQuery | undefined) => U[];
  getNextFetchState: (result: TQuery | undefined) => FetchState;
}) {
  const [fetched, setFetched] = useState<U[] | null>(null);
  const [error, setError] = useState<any>(null);
  const client = useApolloClient();

  const {fetch, stop} = useMemo(() => {
    return new PaginatingDataFetcher({
      fetchData: async (cursor) => {
        const resp = await client.query<TQuery, TVars>({
          variables: {...variables, cursor} as TVars,
          query,
        });

        // Todo align this with the data fetcher better
        return {...getNextFetchState(resp.data), data: getResultArray(resp.data), error: null};
      },
      onData: setFetched,
      onError: setError,
    });
  }, [client, getNextFetchState, getResultArray, query, variables]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  const refreshState = useRefreshAtInterval({
    refresh: fetch,
    intervalMs: 10000,
    leading: true,
  });

  return {fetched, error, refreshState};
}
