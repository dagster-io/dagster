export type QueryResultData<DataType> = {
  data: DataType[] | undefined;
  loading: boolean;
  error: any;
  called: boolean;
};

/**
 * Don't use this function, its an awkward API really meant just for the RunTimeline
 * setQueryData doesn't actually set any data, you have to do it yourself.
 * In the case of the RunTimeline it doesn't set any data because it persists it to a cache instead
 */
export async function fetchPaginatedBucketData<BucketType, DataType, CursorType, ErrorType>({
  buckets,
  fetchData,
  setQueryData,
}: {
  buckets: BucketType[];
  fetchData: (
    bucket: BucketType,
    cursor: CursorType | undefined,
  ) => Promise<{
    hasMore: boolean;
    cursor: CursorType | undefined;
    error: ErrorType;
  }>;
  setQueryData: React.Dispatch<React.SetStateAction<QueryResultData<DataType>>>;
}) {
  setQueryData((queryData) => ({
    ...queryData,
    loading: true,
    called: true,
    error: undefined,
  }));
  try {
    await Promise.all(
      buckets.map((bucket) =>
        fetchPaginatedData<DataType, CursorType, ErrorType>({
          fetchData: async (cursor) => {
            const res = await fetchData(bucket, cursor);
            return {...res, data: []};
          },
        }),
      ),
    );
    setQueryData((queryData) => ({
      ...queryData,
      loading: false,
      called: true,
      error: undefined,
    }));
  } catch (error) {
    setQueryData((queryData) => ({
      ...queryData,
      loading: false,
      called: true,
      error,
    }));
  }
}

export async function fetchPaginatedData<DataType, CursorType, ErrorType>({
  fetchData,
}: {
  fetchData: (cursor: CursorType | undefined) => Promise<{
    data: DataType[];
    hasMore: boolean;
    cursor: CursorType | undefined;
    error: ErrorType;
  }>;
}): Promise<DataType[]> {
  let hasMoreData = true;
  const dataSoFar: DataType[] = [];
  let currentCursor: CursorType | undefined = undefined;

  while (hasMoreData) {
    const {cursor, hasMore, data, error} = await fetchData(currentCursor);
    if (error) {
      throw error;
    }
    for (const item of data) {
      dataSoFar.push(item);
    }
    currentCursor = cursor;
    hasMoreData = hasMore;
  }

  return dataSoFar;
}
