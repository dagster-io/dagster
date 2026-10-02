import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, renderHook, waitFor} from '@testing-library/react';
import {LocationDescriptorObject, MemoryHistory, createMemoryHistory} from 'history';
import {ReactNode} from 'react';
import {Router, useLocation} from 'react-router-dom';

import {InMemoryCache} from '../../apollo-client';
import {buildRun, buildRunsFeedConnection} from '../../graphql/builders';
import possibleTypes from '../../graphql/possibleTypes.generated.json';
import {RunsFeedView} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {RUNS_FEED_QUERY} from '../redesign/RunsFeedQuery';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../redesign/types/RunsFeedQuery.types';
import {useRunsFeed} from '../redesign/useRunsFeed';

type RunsFeedMock = MockedResponse<RunsFeedQuery, RunsFeedQueryVariables>;

const page = (id: string): RunsFeedQuery => ({
  __typename: 'Query',
  runsFeedOrError: {
    ...buildRunsFeedConnection({cursor: id, hasMore: true}),
    results: [
      {
        ...buildRun({id, runId: id, tags: [], assetSelectionCount: 0, assetCheckSelectionCount: 0}),
        assetSelectionPreview: [],
        assetCheckSelectionPreview: [],
      },
    ],
  },
});

const mockPage = (id: string, cursor?: string, filterName?: string): RunsFeedMock => ({
  request: {
    query: RUNS_FEED_QUERY,
    variables: {
      limit: 30,
      filter: filterName ? {pipelineName: filterName} : {},
      view: RunsFeedView.ROOTS,
      ...(cursor ? {cursor} : {}),
    },
  },
  result: {data: page(id)},
});

const createHistory = (entry: LocationDescriptorObject = {pathname: '/runs'}) =>
  createMemoryHistory({initialEntries: [entry]});

const renderFeed = (history: MemoryHistory, mocks: RunsFeedMock[]) => {
  const cache = new InMemoryCache({possibleTypes});
  const wrapper = ({children}: {children: ReactNode}) => (
    <Router history={history}>
      <MockedProvider mocks={mocks} cache={cache}>
        {children}
      </MockedProvider>
    </Router>
  );

  return renderHook(
    () => {
      const filterName = new URLSearchParams(useLocation().search).get('filter');
      return {
        feed: useRunsFeed({
          filter: filterName ? {pipelineName: filterName} : {},
          view: RunsFeedView.ROOTS,
          skip: false,
        }),
        query: useQueryPersistedState<string | undefined>({queryKey: 'q'}),
      };
    },
    {wrapper},
  );
};

// Loads pages "first", "second", and "third", leaving the URL cursor at "second".
const advanceToThirdPage = async (history: MemoryHistory, additionalMocks: RunsFeedMock[] = []) => {
  const view = renderFeed(history, [
    mockPage('first'),
    mockPage('second', 'first'),
    mockPage('third', 'second'),
    ...additionalMocks,
  ]);
  const firstEntryId = () => view.result.current.feed.entries[0]?.id;

  await waitFor(() => expect(firstEntryId()).toBe('first'));

  act(() => view.result.current.feed.paginationProps.advanceCursor());
  await waitFor(() => expect(firstEntryId()).toBe('second'));

  act(() => view.result.current.feed.paginationProps.advanceCursor());
  await waitFor(() => expect(firstEntryId()).toBe('third'));

  return view;
};

// Remounts on page "third" and returns to the previous page.
const remountAndPop = async (history: MemoryHistory) => {
  const {result} = renderFeed(history, [
    mockPage('third', 'second'),
    mockPage('second', 'first'),
    mockPage('first'),
  ]);

  await waitFor(() => expect(result.current.feed.entries[0]?.id).toBe('third'));

  act(() => result.current.feed.paginationProps.popCursor());
  await waitFor(() => expect(result.current.feed.queryResult.loading).toBe(false));

  return result.current.feed.paginationProps.cursor;
};

describe('useCursorPaginatedQuery', () => {
  it('returns to the previous page after browser Back from another page', async () => {
    const history = createHistory();
    const {unmount} = await advanceToThirdPage(history);
    unmount();

    act(() => history.push('/runs/some-run'));
    act(() => history.goBack());
    expect(history.location.search).toBe('?runs_before=second');

    expect(await remountAndPop(history)).toBe('first');
  });

  it('ignores a saved stack whose cursor differs from the URL cursor', async () => {
    const history = createHistory({
      pathname: '/runs',
      search: '?runs_before=second',
      state: {cursorStacks: {runs_before: {cursor: 'other', stack: ['first']}}},
    });

    expect(await remountAndPop(history)).toBeUndefined();
  });

  it('clears the saved stack on reset', async () => {
    const history = createHistory();
    const {result, unmount} = await advanceToThirdPage(history);

    act(() => result.current.feed.paginationProps.reset());
    await waitFor(() => expect(result.current.feed.entries[0]?.id).toBe('first'));
    expect(history.location.state).toEqual({cursorStacks: {}});
    unmount();

    const remounted = renderFeed(history, [mockPage('first')]);
    await waitFor(() => expect(remounted.result.current.feed.entries[0]?.id).toBe('first'));
    expect(remounted.result.current.feed.paginationProps.hasPrevCursor).toBe(false);
  });

  it('does not save cursors from a previous filter after advancing', async () => {
    const history = createHistory();
    const {result, unmount} = await advanceToThirdPage(history, [
      mockPage('filtered-first', undefined, 'filtered'),
      mockPage('filtered-second', 'filtered-first', 'filtered'),
    ]);

    act(() => history.replace('/runs?filter=filtered', history.location.state));
    await waitFor(() => expect(result.current.feed.entries[0]?.id).toBe('filtered-first'));

    act(() => result.current.feed.paginationProps.advanceCursor());
    await waitFor(() => expect(result.current.feed.entries[0]?.id).toBe('filtered-second'));
    unmount();

    const remounted = renderFeed(history, [
      mockPage('filtered-second', 'filtered-first', 'filtered'),
      mockPage('filtered-first', undefined, 'filtered'),
    ]);
    await waitFor(() =>
      expect(remounted.result.current.feed.entries[0]?.id).toBe('filtered-second'),
    );

    act(() => remounted.result.current.feed.paginationProps.popCursor());
    expect(remounted.result.current.feed.paginationProps.cursor).toBeUndefined();
  });

  it('keeps the saved stack through an unrelated query string change', async () => {
    const history = createHistory();
    const {result, unmount} = await advanceToThirdPage(history);

    act(() => result.current.query[1]('search'));
    expect(history.location.search).toBe('?runs_before=second&q=search');
    unmount();

    expect(await remountAndPop(history)).toBe('first');
  });

  it('keeps other location state fields when saving the stack', async () => {
    const history = createHistory({pathname: '/runs', state: {from: 'elsewhere'}});
    await advanceToThirdPage(history);

    expect(history.location.state).toEqual({
      from: 'elsewhere',
      cursorStacks: {runs_before: {cursor: 'second', stack: ['first']}},
    });
  });
});
