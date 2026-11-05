import {MockLink, MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {createMemoryHistory} from 'history';
import {Router} from 'react-router-dom';

import {ApolloLink, InMemoryCache} from '../../../apollo-client';
import {AnalyticsContext} from '../../../app/analytics';
import {buildPythonError, buildRunsFeedConnection} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunStatus, RunsFeedView, RunsFilter} from '../../../graphql/types';
import {shortenId} from '../../../util/shortenId';
import {DagsterTag} from '../../RunTag';
import {buildRunTagFocusMocks} from '../../__fixtures__/RunTagQueries.fixtures';
import {RUNS_FEED_QUERY} from '../RunsFeedQuery';
import {RunsPage} from '../RunsPage';
import {buildRunSummary, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {RunsFeedEntryFragment} from '../types/RunsFeedFragments.types';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../types/RunsFeedQuery.types';

jest.mock('../../../selection/SelectionInput', () => ({
  SelectionAutoCompleteInput: jest.requireActual('../__fixtures__/MockSelectionInput.fixtures')
    .MockSelectionInput,
}));

const FIRST_PAGE_RUN_ID = 'aaaaaaaa-1111-2222-3333-444455556666';
const SECOND_PAGE_RUN_ID = 'bbbbbbbb-1111-2222-3333-444455556666';
const BACKFILL_ID = 'bkfl1234';
const INVALID_SEARCH = `id:"${FIRST_PAGE_RUN_ID}" or job:b`;

type PageOptions = {
  cursor: string;
  hasMore: boolean;
};

const buildRunsFeedQueryResult = (
  results: RunsFeedEntryFragment[],
  {cursor, hasMore}: PageOptions = {cursor: 'end', hasMore: false},
): RunsFeedQuery => ({
  __typename: 'Query',
  runsFeedOrError: {...buildRunsFeedConnection({cursor, hasMore}), results},
});

const runSummary = (id: string) => buildRunSummary({id, runId: id});

type FeedMockOptions = {
  data?: RunsFeedQuery;
  error?: Error;
  filter?: RunsFilter;
  cursor?: string;
  delay?: number;
};

const mockFeed = ({
  data,
  error,
  filter = {},
  cursor,
  delay,
}: FeedMockOptions): MockedResponse<RunsFeedQuery, RunsFeedQueryVariables> => ({
  request: {
    query: RUNS_FEED_QUERY,
    variables: {
      limit: 30,
      filter,
      view: RunsFeedView.RUNS,
      ...(cursor === undefined ? {} : {cursor}),
    },
  },
  result: data ? {data} : undefined,
  error,
  delay,
  maxUsageCount: Number.POSITIVE_INFINITY,
});

const FIRST_PAGE = buildRunsFeedQueryResult([runSummary(FIRST_PAGE_RUN_ID)], {
  cursor: 'first',
  hasMore: true,
});
const SECOND_PAGE = buildRunsFeedQueryResult([runSummary(SECOND_PAGE_RUN_ID)]);
const EMPTY_PAGE = buildRunsFeedQueryResult([]);

const ANALYTICS = {page: () => {}, track: () => {}};

// Button names include the arrow icon's label, so match the visible text at its edge.
const OLDER_BUTTON = {name: /^Older/};
const NEWER_BUTTON = {name: /Newer$/};

const renderPage = (
  path: string,
  mocks: MockedResponse<RunsFeedQuery, RunsFeedQueryVariables>[],
) => {
  const history = createMemoryHistory({initialEntries: [path]});
  const operations: string[] = [];
  const logLink = new ApolloLink((operation, forward) => {
    operations.push(operation.operationName);
    return forward(operation);
  });
  render(
    <AnalyticsContext.Provider value={ANALYTICS}>
      <Router history={history}>
        <MockedProvider
          link={ApolloLink.from([logLink, new MockLink([...mocks, ...buildRunTagFocusMocks()])])}
          cache={new InMemoryCache({possibleTypes})}
        >
          <RunsPage />
        </MockedProvider>
      </Router>
    </AnalyticsContext.Provider>,
  );
  return {history, operations};
};

const findRunLink = (id: string) => screen.findByRole('link', {name: `Run ${shortenId(id)}`});

const findSearchInput = () => screen.findByRole('textbox', {name: 'Search and filter runs'});

const applySearch = async (text: string) => {
  const user = userEvent.setup();
  const input = await findSearchInput();
  await user.clear(input);
  await user.type(input, `${text}{Enter}`);
  return input;
};

describe('RunsPage', () => {
  it('renders entries from the first page', async () => {
    renderPage('/runs', [mockFeed({data: FIRST_PAGE})]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toHaveAttribute(
      'href',
      `/runs/${FIRST_PAGE_RUN_ID}`,
    );
    await waitFor(() => expect(document.title).toBe('Runs | All'));
  });

  it('shows the loading skeleton until the first page arrives', async () => {
    renderPage('/runs', [mockFeed({data: FIRST_PAGE, delay: 50})]);

    expect(await screen.findByRole('status')).toHaveTextContent('Loading runs');
    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(await screen.findByRole('status')).toBeEmptyDOMElement();
  });

  it('moves between pages with Older and Newer', async () => {
    const user = userEvent.setup();
    const {history} = renderPage('/runs', [
      mockFeed({data: FIRST_PAGE}),
      mockFeed({data: SECOND_PAGE, cursor: 'first'}),
    ]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', OLDER_BUTTON));
    expect(await findRunLink(SECOND_PAGE_RUN_ID)).toBeVisible();
    expect(history.location.search).toBe('?runs_before=first');
    expect(await screen.findByRole('button', OLDER_BUTTON)).toBeDisabled();

    await user.click(await screen.findByRole('button', NEWER_BUTTON));
    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(await screen.findByRole('button', NEWER_BUTTON)).toBeDisabled();
  });

  it.each(['runs', 'roots'])('queries individual runs for a view=%s deep link', async (view) => {
    renderPage(`/runs?q[]=job:daily_etl&view=${view}`, [
      mockFeed({data: FIRST_PAGE, filter: {pipelineName: 'daily_etl'}}),
    ]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    await waitFor(() => expect(document.title).toBe('Runs | All'));
  });

  it('lists the runs of a backfill for a backfill search', async () => {
    const backfillRun = buildRunSummary({
      id: SECOND_PAGE_RUN_ID,
      runId: SECOND_PAGE_RUN_ID,
      tags: [tag(DagsterTag.Backfill, BACKFILL_ID)],
    });
    renderPage('/runs', [
      mockFeed({data: EMPTY_PAGE}),
      mockFeed({
        data: buildRunsFeedQueryResult([backfillRun]),
        filter: {tags: [{key: DagsterTag.Backfill, value: BACKFILL_ID}]},
      }),
    ]);

    await screen.findByText('No runs found');
    await applySearch(`backfill:${BACKFILL_ID}`);

    expect(await findRunLink(SECOND_PAGE_RUN_ID)).toBeVisible();
  });

  it.each([
    {
      name: 'queued',
      tokens: ['status:QUEUED'],
      statuses: [RunStatus.QUEUED],
      title: 'Runs | Queued',
    },
    {
      name: 'in-progress',
      tokens: ['status:STARTED', 'status:STARTING', 'status:SUSPENDED', 'status:CANCELING'],
      statuses: [RunStatus.STARTED, RunStatus.STARTING, RunStatus.SUSPENDED, RunStatus.CANCELING],
      title: 'Runs | In progress',
    },
  ])('lists individual runs for the $name status link', async ({tokens, statuses, title}) => {
    const query = tokens.map((token) => `q[]=${token}`).join('&');
    renderPage(`/runs?${query}`, [mockFeed({data: FIRST_PAGE, filter: {statuses}})]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    await waitFor(() => expect(document.title).toBe(title));
  });

  it('starts a new filter on its first page and restores the cursor on Back', async () => {
    const user = userEvent.setup();
    const {history} = renderPage('/runs', [
      mockFeed({data: FIRST_PAGE}),
      mockFeed({data: SECOND_PAGE, cursor: 'first'}),
      mockFeed({data: EMPTY_PAGE, filter: {pipelineName: 'daily_etl'}}),
    ]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', OLDER_BUTTON));
    await findRunLink(SECOND_PAGE_RUN_ID);

    act(() => history.push('/runs?q[]=job:daily_etl'));
    expect(await screen.findByText('No matching runs')).toBeVisible();
    expect(await screen.findByRole('button', NEWER_BUTTON)).toBeDisabled();

    act(() => history.goBack());
    expect(await findRunLink(SECOND_PAGE_RUN_ID)).toBeVisible();
    expect(history.location.search).toBe('?runs_before=first');
  });

  it('applies a search as a new history entry on the first page', async () => {
    const {history} = renderPage(
      '/runs?runs_before=first&view=roots&q[]=job:daily_etl&q[]=status:SUCCESS',
      [
        mockFeed({
          data: SECOND_PAGE,
          filter: {pipelineName: 'daily_etl', statuses: [RunStatus.SUCCESS]},
          cursor: 'first',
        }),
        mockFeed({data: FIRST_PAGE, filter: {statuses: [RunStatus.FAILURE]}}),
      ],
    );

    await findRunLink(SECOND_PAGE_RUN_ID);
    const input = await applySearch('status:failure');

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(history.length).toBe(2);
    const params = new URLSearchParams(history.location.search);
    expect(params.getAll('q[0]')).toEqual(['status:FAILURE']);
    expect(params.has('q[1]')).toBe(false);
    expect(params.get('view')).toBe('roots');
    expect(params.has('runs_before')).toBe(false);
    expect(await findSearchInput()).toBe(input);
    expect(input).toHaveFocus();
  });

  it('restores the previous search and entries after going back', async () => {
    const {history} = renderPage('/runs', [
      mockFeed({data: EMPTY_PAGE}),
      mockFeed({data: FIRST_PAGE, filter: {statuses: [RunStatus.FAILURE]}}),
      mockFeed({data: SECOND_PAGE, filter: {pipelineName: 'daily_etl'}}),
    ]);

    await screen.findByText('No runs found');
    await applySearch('status:failure');
    await findRunLink(FIRST_PAGE_RUN_ID);
    await applySearch('job:daily_etl');
    await findRunLink(SECOND_PAGE_RUN_ID);

    act(() => history.goBack());

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(await findSearchInput()).toHaveValue('status:FAILURE');
  });

  it('does not query for an invalid search', async () => {
    const {history, operations} = renderPage('/runs', [mockFeed({data: FIRST_PAGE})]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    const input = await applySearch(INVALID_SEARCH);

    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');
    expect(input).toHaveValue(INVALID_SEARCH);
    expect(history.length).toBe(1);
    expect(operations.filter((operation) => operation === 'RunsFeedQuery')).toEqual([
      'RunsFeedQuery',
    ]);
  });

  it('shows the search text for a deep link with several legacy tokens', async () => {
    renderPage('/runs?q[]=pipeline:daily_etl&q[]=tag:team=data&q[]=status:FAILURE', [
      mockFeed({
        data: FIRST_PAGE,
        filter: {
          pipelineName: 'daily_etl',
          tags: [{key: 'team', value: 'data'}],
          statuses: [RunStatus.FAILURE],
        },
      }),
    ]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(await findSearchInput()).toHaveValue(
      'status:FAILURE and job:daily_etl and tag:team=data',
    );
  });

  it.each([
    {
      name: 'runs',
      path: '/runs',
      filter: {},
      title: 'No runs found',
    },
    {
      name: 'filtered runs',
      path: '/runs?q[]=job:daily_etl',
      filter: {pipelineName: 'daily_etl'},
      title: 'No matching runs',
    },
  ])('shows the empty state for $name', async ({path, filter, title}) => {
    renderPage(path, [mockFeed({data: EMPTY_PAGE, filter})]);

    expect(await screen.findByText(title)).toBeVisible();
  });

  it('labels the created-date control from a legacy date link and leaves dates out of the search', async () => {
    renderPage('/runs?q[]=created_date_after:1700000000&q[]=job:daily_etl', [
      mockFeed({data: FIRST_PAGE, filter: {createdAfter: 1700000000, pipelineName: 'daily_etl'}}),
    ]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(
      await screen.findByRole('button', {name: 'Created date: After Nov 14, 2023'}),
    ).toBeVisible();
    expect(await findSearchInput()).toHaveValue('job:daily_etl');
  });

  it('keeps the date range in the URL when a search is applied', async () => {
    const {history} = renderPage('/runs?q[]=created_date_after:1700000000', [
      mockFeed({data: EMPTY_PAGE, filter: {createdAfter: 1700000000}}),
      mockFeed({
        data: FIRST_PAGE,
        filter: {createdAfter: 1700000000, statuses: [RunStatus.FAILURE]},
      }),
    ]);

    await screen.findByText('No matching runs');
    await applySearch('status:failure');

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    const params = new URLSearchParams(history.location.search);
    expect(params.getAll('q[0]')).toEqual(['status:FAILURE']);
    expect(params.getAll('q[1]')).toEqual(['created_date_after:1700000000']);
  });

  it('keeps an invalid search draft and its error when a date range is picked', async () => {
    const user = userEvent.setup();
    const {history} = renderPage('/runs?q[]=created_date_after:1700000000', [
      mockFeed({data: EMPTY_PAGE, filter: {createdAfter: 1700000000}}),
      mockFeed({data: FIRST_PAGE}),
    ]);

    await screen.findByText('No matching runs');
    const input = await applySearch(INVALID_SEARCH);
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');

    await user.click(await screen.findByRole('button', {name: 'Created date: After Nov 14, 2023'}));
    await user.click(await screen.findByRole('menuitem', {name: 'All time'}));

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    expect(history.location.search).toBe('');
    expect(input).toHaveValue(INVALID_SEARCH);
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');
  });

  it('shows a request error and keeps the pagination controls', async () => {
    renderPage('/runs', [mockFeed({error: new Error('Network down')})]);

    expect(await screen.findByText('Unexpected error')).toBeVisible();
    expect(await screen.findByRole('button', OLDER_BUTTON)).toBeDisabled();
  });

  it('shows a Python error and keeps the pagination controls', async () => {
    const error = buildPythonError({message: 'Feed query failed', stack: [], errorChain: []});
    renderPage('/runs', [mockFeed({data: {__typename: 'Query', runsFeedOrError: error}})]);

    expect(await screen.findByText('Feed query failed')).toBeVisible();
    expect(await screen.findByRole('button', OLDER_BUTTON)).toBeDisabled();
    expect(screen.queryByText('No runs found')).not.toBeInTheDocument();
  });
});
