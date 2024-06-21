import {OperationVariables, useApolloClient} from '@apollo/client';
import {DocumentNode} from 'graphql';
import {useEffect, useMemo, useState} from 'react';

import {useRefreshAtInterval} from '../app/QueryRefresh';

type FetchResult<DataType, CursorType, ErrorType> = {
  data: DataType[];
  hasMore: boolean;
  cursor: CursorType | undefined;
  error: ErrorType | undefined;
};

type FetcherFunction<DataType, CursorType, ErrorType> = (
  cursor: CursorType | undefined,
) => Promise<FetchResult<DataType, CursorType, ErrorType>>;

class AccumulatingDataFetcher<DataType, CursorType, ErrorType> {
  private fetchData: FetcherFunction<DataType, CursorType, ErrorType>;
  private onData: (data: DataType[]) => void;
  private onError?: (error: ErrorType) => void;

  private hasMoreData = true;
  private dataSoFar: DataType[] = [];
  private currentCursor: CursorType | undefined = undefined;
  private fetchPromise?: Promise<void>;
  private stopped: boolean = false;

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

  fetch = async () => {
    if (this.fetchPromise) {
      return await this.fetchPromise;
    }
    this.fetchPromise = new Promise(async (res) => {
      // make at least one request
      this.hasMoreData = true;

      // continue requesting with updated cursors + accumulating data until
      // stop() is called or hasMore=false.
      while (this.hasMoreData && !this.stopped) {
        const {cursor, hasMore, data, error} = await this.fetchData(this.currentCursor);
        if (this.stopped) {
          break;
        }
        if (error) {
          this.onError?.(error);
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
  };

  stop = () => {
    this.stopped = true;
  };
}

export function useCursorAccumulatedQuery<
  TQuery,
  TVars extends OperationVariables & {cursor?: CursorType},
  DataType,
  ErrorType = unknown,
  CursorType = TVars['cursor'],
>({
  query,
  variables,
  getResult,
}: {
  query: DocumentNode;
  variables: Omit<TVars, 'cursor'>;
  getResult: (responseData: TQuery) => FetchResult<DataType, CursorType, ErrorType>;
}) {
  const [fetched, setFetched] = useState<DataType[] | null>(null);
  const [error, setError] = useState<ErrorType | null>(null);
  const client = useApolloClient();

  const {stop, fetch} = useMemo(() => {
    return new AccumulatingDataFetcher({
      fetchData: async (cursor) => {
        const resp = await client.query<TQuery, TVars>({
          variables: {...variables, cursor} as TVars,
          query,
        });
        return getResult(resp.data);
      },
      onData: setFetched,
      onError: setError,
    });
  }, [client, query, variables, getResult]);

  useEffect(() => {
    return stop;
  }, [stop]);

  const refreshState = useRefreshAtInterval({
    refresh: fetch,
    intervalMs: 10000,
    leading: true,
  });

  return {fetched, error, refreshState};
}
