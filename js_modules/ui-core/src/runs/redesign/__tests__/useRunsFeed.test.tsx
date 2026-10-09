import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, cleanup, renderHook, waitFor} from '@testing-library/react';
import {createMemoryHistory} from 'history';
import {ReactNode} from 'react';
import {Router} from 'react-router-dom';

import {InMemoryCache} from '../../../apollo-client';
import {buildPythonError, buildRun, buildRunsFeedConnection} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunsFeedView} from '../../../graphql/types';
import {RUNS_FEED_QUERY} from '../RunsFeedQuery';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../types/RunsFeedQuery.types';
import {RunsFeedOptions, useRunsFeed} from '../useRunsFeed';

const defaultOptions: RunsFeedOptions = {filter: {}, view: RunsFeedView.ROOTS, skip: false};

const page = (id: string, hasMore = true): RunsFeedQuery => ({
  __typename: 'Query',
  runsFeedOrError: {
    ...buildRunsFeedConnection({cursor: id, hasMore}),
    results: [
      {
        ...buildRun({id, runId: id, tags: [], assetSelectionCount: 0, assetCheckSelectionCount: 0}),
        assetSelectionPreview: [],
        assetCheckSelectionPreview: [],
      },
    ],
  },
});

const mockPage = (
  data: RunsFeedQuery,
  variables: Partial<RunsFeedQueryVariables> = {},
): MockedResponse<RunsFeedQuery, RunsFeedQueryVariables> => ({
  request: {
    query: RUNS_FEED_QUERY,
    variables: {limit: 30, filter: {}, view: RunsFeedView.ROOTS, ...variables},
  },
  result: {data},
});

const renderFeed = (
  mocks: MockedResponse<RunsFeedQuery, RunsFeedQueryVariables>[],
  options = defaultOptions,
) => {
  const history = createMemoryHistory({initialEntries: ['/runs']});
  const cache = new InMemoryCache({possibleTypes});
  const wrapper = ({children}: {children: ReactNode}) => (
    <Router history={history}>
      <MockedProvider mocks={mocks} cache={cache}>
        {children}
      </MockedProvider>
    </Router>
  );

  return {
    ...renderHook((feedOptions: RunsFeedOptions) => useRunsFeed(feedOptions), {
      initialProps: options,
      wrapper,
    }),
    history,
  };
};

describe('useRunsFeed', () => {
  beforeEach(() => jest.useFakeTimers());

  afterEach(() => {
    cleanup();
    jest.useRealTimers();
  });

  it('polls the current cursor page without accumulating entries', async () => {
    const refreshed = jest.fn(() => ({data: page('updated', false)}));
    const {result, history} = renderFeed([
      mockPage(page('first')),
      mockPage(page('second'), {cursor: 'first'}),
      {...mockPage(page('updated', false), {cursor: 'first'}), result: refreshed, delay: 500},
    ]);

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));

    act(() => result.current.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('second'));

    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(result.current.queryResult.loading).toBe(true);
    expect(result.current.entries.map(({id}) => id)).toEqual(['second']);

    await act(() => jest.advanceTimersByTimeAsync(1000));
    expect(refreshed).toHaveBeenCalledTimes(1);
    expect(result.current.entries.map(({id}) => id)).toEqual(['updated']);
    expect(result.current.paginationProps).toMatchObject({cursor: 'first', hasNextCursor: false});
    expect(history.location.search).toContain('runs_before=first');
  });

  it('clears pagination only when reset is called', async () => {
    const {result} = renderFeed([
      mockPage(page('first')),
      mockPage(page('second'), {cursor: 'first'}),
      mockPage(page('third'), {cursor: 'second'}),
    ]);

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));

    act(() => result.current.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('second'));

    act(() => result.current.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('third'));

    act(() => result.current.paginationProps.reset());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));
    expect(result.current.paginationProps).toMatchObject({cursor: undefined, hasPrevCursor: false});
  });

  it('retains previous-page navigation after browser history returns to a cursor', async () => {
    const {result, history} = renderFeed([
      mockPage(page('first')),
      mockPage(page('second'), {cursor: 'first'}),
      mockPage(page('third'), {cursor: 'second'}),
    ]);

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));

    act(() => result.current.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('second'));

    act(() => result.current.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('third'));

    act(() => history.push('/runs'));
    act(() => history.goBack());
    expect(result.current.paginationProps.cursor).toBe('second');

    act(() => result.current.paginationProps.popCursor());
    expect(result.current.paginationProps.cursor).toBe('first');
  });

  it.each([
    {name: 'filters', variables: {filter: {pipelineName: 'broken'}}},
    {name: 'view', variables: {view: RunsFeedView.RUNS}},
  ])('does not retain entries when the caller changes $name', async ({variables}) => {
    const error = buildPythonError({message: 'Query failed', stack: [], errorChain: []});
    const {result, rerender} = renderFeed([
      mockPage(page('first')),
      mockPage({__typename: 'Query', runsFeedOrError: error}, variables),
    ]);

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));

    rerender({...defaultOptions, ...variables});
    expect(result.current.entries).toEqual([]);

    await waitFor(() => expect(result.current.error?.message).toBe('Query failed'));
    expect(result.current.entries).toEqual([]);
  });

  it('does not fetch or poll while skipped', async () => {
    const fetched = jest.fn(() => ({data: page('first')}));
    const {result, rerender} = renderFeed(
      [{...mockPage(page('first')), result: fetched, maxUsageCount: Infinity}],
      {...defaultOptions, skip: true},
    );

    await act(() => jest.advanceTimersByTimeAsync(30000));
    expect(fetched).not.toHaveBeenCalled();
    expect(result.current.entries).toEqual([]);

    rerender(defaultOptions);
    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));
    expect(fetched).toHaveBeenCalledTimes(1);

    rerender({...defaultOptions, skip: true});
    await act(() => jest.advanceTimersByTimeAsync(30000));
    expect(fetched).toHaveBeenCalledTimes(1);
  });

  it('prefers a current network error over a cached Python error', async () => {
    const error = buildPythonError({message: 'Old Python error', stack: [], errorChain: []});
    const {result} = renderFeed([
      mockPage({__typename: 'Query', runsFeedOrError: error}),
      {...mockPage(page('unused')), result: undefined, error: new Error('Offline now')},
    ]);

    await waitFor(() => expect(result.current.error?.message).toBe('Old Python error'));

    await act(async () => {
      const rejected = result.current.queryResult.refetch().catch((caught) => caught);

      await jest.advanceTimersByTimeAsync(0);
      expect(await rejected).toMatchObject({message: 'Offline now'});
    });

    expect(result.current.queryResult.error?.message).toBe('Offline now');
    expect(result.current.error?.message).toBe('Offline now');
  });

  it('keeps current-page data after a failed refetch and clears the error after recovery', async () => {
    const failed = {...mockPage(page('unused')), result: undefined, error: new Error('Offline')};
    const {result} = renderFeed([mockPage(page('first')), failed, mockPage(page('recovered'))]);

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('first'));

    await act(async () => {
      const rejected = result.current.queryResult.refetch().catch((caught) => caught);

      await jest.advanceTimersByTimeAsync(0);
      expect(await rejected).toMatchObject({message: 'Offline'});
    });

    expect(result.current.error?.message).toBe('Offline');
    expect(result.current.entries[0]?.id).toBe('first');

    await act(async () => {
      const refetch = result.current.queryResult.refetch();

      await jest.advanceTimersByTimeAsync(0);
      await refetch;
    });

    await waitFor(() => expect(result.current.entries[0]?.id).toBe('recovered'));
    expect(result.current.error).toBeUndefined();
  });
});
