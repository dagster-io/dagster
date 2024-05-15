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
    data,
    loading: true,
    called: true,
    error: undefined,
  }));

  try {
    const results = await Promise.all(
      buckets.map(
        (bucket) =>
          new Promise<DataType[]>(async (res, rej) => {
            let hasMoreData = true;
            const dataSoFar: DataType[] = [];
            let currentCursor: CursorType | undefined = undefined;
            while (hasMoreData) {
              const {cursor, hasMore, data, error} = await fetchData(bucket, currentCursor);
              if (error) {
                rej(error);
                return;
              }
              dataSoFar.push(...data);
              currentCursor = cursor;
              hasMoreData = hasMore;
            }
            res(dataSoFar);
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
    setQueryData(({data}) => ({
      data,
      loading: false,
      called: true,
      error,
    }));
  }
}
