import {DocumentNode} from 'graphql';
import {useEffect, useMemo, useState} from 'react';

import {OperationVariables, useApolloClient} from '../apollo-client';

export type AccumulatingFetchResult<DataType, CursorType, ErrorType> = {
  data: DataType[];
  hasMore: boolean;
  cursor: CursorType | undefined;
  error: ErrorType | undefined;
};

type FetcherFunction<DataType, CursorType, ErrorType> = (
  cursor: CursorType | undefined,
) => Promise<AccumulatingFetchResult<DataType, CursorType, ErrorType>>;

class AccumulatingDataFetcher<DataType, CursorType, ErrorType> {
  private fetchData: FetcherFunction<DataType, CursorType, ErrorType>;
  private onData: (data: DataType[]) => void;
  private onError?: (error: ErrorType) => void;

  private maxPages?: number;

  private hasMoreData = true;
  private dataSoFar: DataType[] = [];
  private currentCursor: CursorType | undefined = undefined;
  private pagesFetched = 0;
  private fetchPromise?: Promise<void>;
  private stopped: boolean = false;

  constructor({
    fetchData,
    onData,
    onError,
    initialCursor,
    maxPages,
  }: {
    fetchData: FetcherFunction<DataType, CursorType, ErrorType>;
    onData: (data: DataType[]) => void;
    onError?: (error: ErrorType) => void;
    initialCursor?: CursorType;
    maxPages?: number;
  }) {
    this.fetchData = fetchData;
    this.onData = onData;
    this.onError = onError;
    this.currentCursor = initialCursor;
    this.maxPages = maxPages;
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
        const isFirstPage = this.pagesFetched === 0;
        const {cursor, hasMore, data, error} = await this.fetchData(this.currentCursor);
        if (this.stopped) {
          break;
        }
        if (error) {
          this.onError?.(error);
          break;
        }
        this.pagesFetched += 1;
        this.currentCursor = cursor;
        this.hasMoreData = hasMore && (!this.maxPages || this.pagesFetched < this.maxPages);

        // Emit an onData event - note that we always call onData after loading
        // the first page, even if there is no data to display, so that consumers
        // can implement a state transition from loading => empty.
        if (isFirstPage || data.length > 0) {
          this.dataSoFar = this.dataSoFar.concat(data);
          this.onData(this.dataSoFar);
        }
      }
      res();
    });
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
  initialCursor,
  maxPages,
}: {
  query: DocumentNode;
  variables: Omit<TVars, 'cursor'>;
  // Important: getResult must be memoized!
  getResult: (responseData: TQuery) => AccumulatingFetchResult<DataType, CursorType, ErrorType>;
  // Cursor to send with the first request, for queries whose first page is already bounded.
  initialCursor?: CursorType;
  // Stop after this many requests, even if the server reports more data.
  maxPages?: number;
}) {
  const [fetched, setFetched] = useState<DataType[] | null>(null);
  const [error, setError] = useState<ErrorType | null>(null);
  const client = useApolloClient();

  const variablesJSON = JSON.stringify(variables || {});
  const {stop, fetch} = useMemo(() => {
    return new AccumulatingDataFetcher({
      fetchData: async (cursor) => {
        const resp = await client.query<TQuery, TVars>({
          variables: {...JSON.parse(variablesJSON), cursor} as TVars,
          query,
        });
        return getResult(resp.data);
      },
      onData: setFetched,
      onError: setError,
      initialCursor,
      maxPages,
    });
  }, [client, query, variablesJSON, getResult, initialCursor, maxPages]);

  useEffect(() => {
    void fetch();
    return stop;
  }, [fetch, stop]);

  return {fetched, error, fetch};
}
