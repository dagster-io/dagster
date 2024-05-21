export type QueryResultData<DataType> = {
  data: DataType[] | undefined;
  loading: boolean;
  error: any;
  called: boolean;
};

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
    data: DataType[];
    hasMore: boolean;
    cursor: CursorType | undefined;
    error: ErrorType;
  }>;
  setQueryData: React.Dispatch<React.SetStateAction<QueryResultData<DataType>>>;
}) {
  setQueryData(({data}) => ({
    data, // preserve existing data
    loading: true,
    called: true,
    error: undefined,
  }));
  try {
    const results = await Promise.all(
      buckets.map((bucket) =>
        fetchPaginatedData<DataType, CursorType, ErrorType>({
          fetchData: (cursor) => fetchData(bucket, cursor),
        }),
      ),
    );
    setQueryData({
      data: results.flat(),
      loading: false,
      called: true,
      error: undefined,
    });
  } catch (error) {
    debugger;
    console.error(error);
    setQueryData(({data}) => ({
      data, // preserve existing data
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
    try {
      const {cursor, hasMore, data, error} = await fetchData(currentCursor);
      if (error) {
        throw error;
      }
      dataSoFar.push(...data);
      currentCursor = cursor;
      hasMoreData = hasMore;
    } catch (e) {
      throw e;
      hasMoreData = false;
    }
  }

  return dataSoFar;
}
