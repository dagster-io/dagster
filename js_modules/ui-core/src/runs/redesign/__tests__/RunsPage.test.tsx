import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {createMemoryHistory} from 'history';
import {Router} from 'react-router-dom';

import {InMemoryCache} from '../../../apollo-client';
import {AnalyticsContext} from '../../../app/analytics';
import {buildPythonError, buildRunsFeedConnection} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunStatus, RunsFeedView, RunsFilter} from '../../../graphql/types';
import {RUNS_FEED_QUERY} from '../RunsFeedQuery';
import {RunsPage} from '../RunsPage';
import {buildBackfillSummary, buildRunSummary} from '../__fixtures__/RunsFeedEntries.fixtures';
import {RunsFeedEntryFragment} from '../types/RunsFeedFragments.types';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../types/RunsFeedQuery.types';

const FIRST_PAGE_RUN_ID = 'aaaaaaaa-1111-2222-3333-444455556666';
const SECOND_PAGE_RUN_ID = 'bbbbbbbb-1111-2222-3333-444455556666';
const BACKFILL_ID = 'bkfl1234';

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
  view?: RunsFeedView;
  cursor?: string;
  delay?: number;
};

const mockFeed = ({
  data,
  error,
  filter = {},
  view = RunsFeedView.ROOTS,
  cursor,
  delay,
}: FeedMockOptions): MockedResponse<RunsFeedQuery, RunsFeedQueryVariables> => ({
  request: {
    query: RUNS_FEED_QUERY,
    variables: {limit: 30, filter, view, ...(cursor === undefined ? {} : {cursor})},
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
  render(
    <AnalyticsContext.Provider value={ANALYTICS}>
      <Router history={history}>
        <MockedProvider mocks={mocks} cache={new InMemoryCache({possibleTypes})}>
          <RunsPage />
        </MockedProvider>
      </Router>
    </AnalyticsContext.Provider>,
  );
  return {history};
};

const findRunLink = (id: string) => screen.findByRole('link', {name: `Run ${id.slice(0, 8)}`});

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

  it('queries the filter and view from a deep link', async () => {
    renderPage('/runs?q[]=job:daily_etl&view=backfills', [
      mockFeed({
        data: buildRunsFeedQueryResult([buildBackfillSummary({id: BACKFILL_ID})]),
        filter: {pipelineName: 'daily_etl'},
        view: RunsFeedView.BACKFILLS,
      }),
    ]);

    expect(await screen.findByRole('link', {name: `Backfill ${BACKFILL_ID}`})).toBeVisible();
    await waitFor(() => expect(document.title).toBe('Runs | All backfills'));
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
      tokens: ['status:STARTED', 'status:STARTING', 'status:CANCELING'],
      statuses: [RunStatus.STARTED, RunStatus.STARTING, RunStatus.CANCELING],
      title: 'Runs | In progress',
    },
  ])('lists individual runs for the $name status link', async ({tokens, statuses, title}) => {
    const query = tokens.map((token) => `q[]=${token}`).join('&');
    renderPage(`/runs?${query}`, [
      mockFeed({data: FIRST_PAGE, filter: {statuses}, view: RunsFeedView.RUNS}),
    ]);

    expect(await findRunLink(FIRST_PAGE_RUN_ID)).toBeVisible();
    await waitFor(() => expect(document.title).toBe(title));
  });

  it('starts a new view on its first page and restores the cursor on Back', async () => {
    const user = userEvent.setup();
    const {history} = renderPage('/runs', [
      mockFeed({data: FIRST_PAGE}),
      mockFeed({data: SECOND_PAGE, cursor: 'first'}),
      mockFeed({
        data: buildRunsFeedQueryResult([buildBackfillSummary({id: BACKFILL_ID})]),
        view: RunsFeedView.BACKFILLS,
      }),
    ]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', OLDER_BUTTON));
    await findRunLink(SECOND_PAGE_RUN_ID);

    act(() => history.push('/runs?view=backfills'));
    expect(await screen.findByRole('link', {name: `Backfill ${BACKFILL_ID}`})).toBeVisible();
    expect(await screen.findByRole('button', NEWER_BUTTON)).toBeDisabled();

    act(() => history.goBack());
    expect(await findRunLink(SECOND_PAGE_RUN_ID)).toBeVisible();
    expect(history.location.search).toBe('?runs_before=first');
  });

  it.each([
    {
      name: 'runs',
      path: '/runs',
      filter: {},
      view: RunsFeedView.ROOTS,
      title: 'No runs found',
    },
    {
      name: 'filtered runs',
      path: '/runs?q[]=job:daily_etl',
      filter: {pipelineName: 'daily_etl'},
      view: RunsFeedView.ROOTS,
      title: 'No matching runs',
    },
  ])('shows the empty state for $name', async ({path, filter, view, title}) => {
    renderPage(path, [mockFeed({data: EMPTY_PAGE, filter, view})]);

    expect(await screen.findByText(title)).toBeVisible();
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
