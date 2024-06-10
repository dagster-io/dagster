import {useState} from 'react';

import {fetchPaginatedBucketData} from '../fetchPaginatedBucketData';

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useState: jest.fn(),
}));

type DataType = {id: number};
type BucketType = string;
type CursorType = string | undefined;

describe('fetchPaginatedBucketData', () => {
  let setQueryDataMock = jest.fn();
  let fetchDataMock: jest.MockedFunction<
    (
      bucket: BucketType,
      cursor: CursorType | undefined,
    ) => Promise<{
      data: DataType[];
      hasMore: boolean;
      cursor: CursorType | undefined;
      error: any;
    }>
  >;

  beforeEach(() => {
    setQueryDataMock = jest.fn();
    fetchDataMock = jest.fn();
    jest.clearAllMocks();
  });

  it('should set loading state to true initially', async () => {
    const buckets: BucketType[] = ['bucket1', 'bucket2'];
    fetchDataMock.mockResolvedValue({
      data: [{id: 999}],
      hasMore: false,
      cursor: undefined,
      error: undefined,
    });

    const setStateMock = jest.fn();
    (useState as jest.Mock).mockImplementation((initial) => [initial, setStateMock]);

    await fetchPaginatedBucketData<BucketType, DataType, CursorType, any>({
      buckets,
      fetchData: fetchDataMock,
      setQueryData: setQueryDataMock,
    });

    expect(
      setQueryDataMock.mock.calls[0][0]!({data: [{id: 1}], hasMore: false, cursor: undefined}),
    ).toEqual({
      called: true,
      cursor: undefined,
      data: [{id: 1}],
      error: undefined,
      hasMore: false,
      loading: true,
    });

    const data = [{id: 999}, {id: 999}];

    expect(setQueryDataMock.mock.calls[1][0]({data})).toEqual({
      loading: false,
      called: true,
      error: undefined,
      data,
    });
  });

  it('should fetch data for each bucket', async () => {
    const buckets: BucketType[] = ['bucket1', 'bucket2'];
    const dataForBucket1: DataType[] = [{id: 1}, {id: 2}];
    const dataForBucket2: DataType[] = [{id: 3}, {id: 4}];

    fetchDataMock
      .mockResolvedValueOnce({
        data: dataForBucket1,
        hasMore: false,
        cursor: undefined,
        error: undefined,
      })
      .mockResolvedValueOnce({
        data: dataForBucket2,
        hasMore: false,
        cursor: undefined,
        error: undefined,
      });

    await fetchPaginatedBucketData<BucketType, DataType, CursorType, any>({
      buckets,
      fetchData: fetchDataMock,
      setQueryData: setQueryDataMock,
    });

    expect(fetchDataMock).toHaveBeenCalledTimes(buckets.length);
    expect(fetchDataMock).toHaveBeenCalledWith('bucket1', undefined);
    expect(fetchDataMock).toHaveBeenCalledWith('bucket2', undefined);
  });

  it('should accumulate data across multiple pages', async () => {
    const buckets: BucketType[] = ['bucket1'];
    const dataPage1: DataType[] = [{id: 1}];
    const dataPage2: DataType[] = [{id: 2}];

    fetchDataMock
      .mockResolvedValueOnce({
        data: dataPage1,
        hasMore: true,
        cursor: 'cursor1',
        error: undefined,
      })
      .mockResolvedValueOnce({
        data: dataPage2,
        hasMore: false,
        cursor: undefined,
        error: undefined,
      });

    await fetchPaginatedBucketData<BucketType, DataType, CursorType, any>({
      buckets,
      fetchData: fetchDataMock,
      setQueryData: setQueryDataMock,
    });

    expect(fetchDataMock).toHaveBeenCalledWith('bucket1', undefined);
    expect(fetchDataMock).toHaveBeenCalledWith('bucket1', 'cursor1');

    const calls = setQueryDataMock.mock.calls;
    expect(calls.length).toEqual(2);
    expect(calls[calls.length - 1]![0]({})).toEqual({
      loading: false,
      called: true,
      error: undefined,
    });
  });

  it('should handle fetchData returning an error', async () => {
    const buckets: BucketType[] = ['bucket1'];
    const error = new Error('Fetch error');

    fetchDataMock.mockResolvedValueOnce({
      data: [],
      hasMore: false,
      cursor: undefined,
      error,
    });

    await fetchPaginatedBucketData<BucketType, DataType, CursorType, any>({
      buckets,
      fetchData: fetchDataMock,
      setQueryData: setQueryDataMock,
    });

    const data = [{id: 1}];
    const calls = setQueryDataMock.mock.calls;
    expect(calls.length).toEqual(2);
    expect(calls[calls.length - 1]![0]({data})).toEqual({
      data,
      loading: false,
      called: true,
      error,
    });
  });

  it('should update the state with the fetched data', async () => {
    const buckets: BucketType[] = ['bucket1'];
    const data: DataType[] = [{id: 1}];

    fetchDataMock.mockResolvedValueOnce({
      data,
      hasMore: false,
      cursor: undefined,
      error: undefined,
    });

    await fetchPaginatedBucketData<BucketType, DataType, CursorType, any>({
      buckets,
      fetchData: fetchDataMock,
      setQueryData: setQueryDataMock,
    });

    const calls = setQueryDataMock.mock.calls;
    expect(calls.length).toEqual(2);
    expect(calls[calls.length - 1]![0]({data})).toEqual({
      data,
      loading: false,
      called: true,
      error: undefined,
    });
  });
});
