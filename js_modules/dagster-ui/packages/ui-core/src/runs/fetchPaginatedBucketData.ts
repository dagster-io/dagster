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

  const fetchDataForBucket = async (bucket: BucketType): Promise<DataType[]> => {
    let hasMoreData = true;
    const dataSoFar: DataType[] = [];
    let currentCursor: CursorType | undefined = undefined;

    while (hasMoreData) {
      const {cursor, hasMore, data, error} = await fetchData(bucket, currentCursor);
      if (error) {
        throw error;
      }
      dataSoFar.push(...data);
      currentCursor = cursor;
      hasMoreData = hasMore;
    }

    return dataSoFar;
  };

  try {
    const results = await Promise.all(buckets.map(fetchDataForBucket));

    setQueryData({
      data: results.flat(),
      loading: false,
      called: true,
      error: undefined,
    });
  } catch (error) {
    setQueryData(({data}) => ({
      data, // preserve existing data
      loading: false,
      called: true,
      error,
    }));
  }
}
