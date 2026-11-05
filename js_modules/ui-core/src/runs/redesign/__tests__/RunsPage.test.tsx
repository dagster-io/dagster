import {MockLink, MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {createMemoryHistory} from 'history';
import {Router} from 'react-router-dom';

import {ApolloLink, InMemoryCache} from '../../../apollo-client';
import {AnalyticsContext} from '../../../app/analytics';
import {IsMobileContext} from '../../../app/layout/IsMobileContext';
import {
  buildDeletePipelineRunSuccess,
  buildPythonError,
  buildQuery,
  buildRuns,
  buildRunsFeedConnection,
} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunStatus, RunsFeedView, RunsFilter} from '../../../graphql/types';
import {buildMutationMock} from '../../../testing/mocking';
import {shortenId} from '../../../util/shortenId';
import {DagsterTag} from '../../RunTag';
import {DELETE_MUTATION} from '../../RunUtils';
import {TERMINATE_BATCH_QUERY} from '../../TerminateAllRunsDialog';
import {buildRunTagFocusMocks} from '../../__fixtures__/RunTagQueries.fixtures';
import {DeleteMutation, DeleteMutationVariables} from '../../types/RunUtils.types';
import {
  TerminateBatchQuery,
  TerminateBatchQueryVariables,
} from '../../types/TerminateAllRunsDialog.types';
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
const THIRD_RUN_ID = 'cccccccc-1111-2222-3333-444455556666';
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

const runSummary = (id: string) => buildRunSummary({id, runId: id, hasDeletePermission: true});

type FeedMockOptions = {
  data?: RunsFeedQuery;
  error?: Error;
  filter?: RunsFilter;
  cursor?: string;
  delay?: number;
  maxUsageCount?: number;
};

const mockFeed = ({
  data,
  error,
  filter = {},
  cursor,
  delay,
  maxUsageCount = Number.POSITIVE_INFINITY,
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
  maxUsageCount,
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

const mockTerminateBatch = (
  filter: RunsFilter,
): MockedResponse<TerminateBatchQuery, TerminateBatchQueryVariables> => ({
  request: {query: TERMINATE_BATCH_QUERY, variables: {filter, limit: 1000}},
  result: {data: buildQuery({pipelineRunsOrError: buildRuns({results: []})})},
});

const renderPage = (path: string, mocks: MockedResponse[], isMobile = false) => {
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
          <IsMobileContext.Provider value={isMobile}>
            <RunsPage />
          </IsMobileContext.Provider>
        </MockedProvider>
      </Router>
    </AnalyticsContext.Provider>,
  );
  return {history, operations};
};

const findRunLink = (id: string) => screen.findByRole('link', {name: `Run ${shortenId(id)}`});

const TERMINATE_ALL_BUTTON = {name: 'Terminate all queued and in-progress runs'};
const DISABLED_REASON = 'The filter excludes queued and in-progress runs';
const FORCE_OPTION = {name: 'Force termination immediately'};

const TERMINABLE_STATUSES = [
  RunStatus.QUEUED,
  RunStatus.STARTED,
  RunStatus.STARTING,
  RunStatus.SUSPENDED,
  RunStatus.CANCELING,
];

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

describe('RunsPage terminate all', () => {
  const openDialog = async (user: ReturnType<typeof userEvent.setup>) => {
    await findRunLink(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', TERMINATE_ALL_BUTTON));
  };

  // The dialog queries the runs matching its filter, so a mock for that exact filter proves it.
  const confirmTerminate = async (user: ReturnType<typeof userEvent.setup>, name: string) => {
    await user.click(await screen.findByRole('button', {name}));
    await user.click(await screen.findByRole('button', {name: 'Done'}));
  };

  it('terminates queued and in-progress runs, keeping the other filters', async () => {
    const user = userEvent.setup();
    const filter = {pipelineName: 'daily_etl'};
    renderPage('/runs?q[]=job:daily_etl', [
      mockFeed({data: FIRST_PAGE, filter}),
      mockTerminateBatch({...filter, statuses: TERMINABLE_STATUSES}),
    ]);

    await openDialog(user);
    expect(await screen.findByRole('checkbox', FORCE_OPTION)).toBeVisible();
    await confirmTerminate(user, 'Terminate all');
  });

  it('hides the force option when only queued runs are targeted', async () => {
    const user = userEvent.setup();
    const filter = {pipelineName: 'daily_etl', statuses: [RunStatus.QUEUED]};
    renderPage('/runs?q[]=status:QUEUED&q[]=job:daily_etl', [
      mockFeed({data: FIRST_PAGE, filter}),
      mockTerminateBatch(filter),
    ]);

    await openDialog(user);
    expect(await screen.findByText(/All matching runs will be terminated/)).toBeVisible();
    expect(screen.queryByRole('checkbox', FORCE_OPTION)).not.toBeInTheDocument();
    await confirmTerminate(user, 'Force terminate all');
  });

  it('terminates only the queued and in-progress part of a mixed status filter', async () => {
    const user = userEvent.setup();
    renderPage('/runs?q[]=status:QUEUED&q[]=status:FAILURE', [
      mockFeed({data: FIRST_PAGE, filter: {statuses: [RunStatus.QUEUED, RunStatus.FAILURE]}}),
      mockTerminateBatch({statuses: [RunStatus.QUEUED]}),
    ]);

    await openDialog(user);
    await user.click(await screen.findByRole('button', {name: 'Force terminate all'}));

    expect(await screen.findByRole('button', {name: 'Done'})).toBeVisible();
  });

  it.each([RunStatus.FAILURE, RunStatus.NOT_STARTED])(
    'is disabled with its reason when the filter is %s',
    async (status) => {
      renderPage(`/runs?q[]=status:${status}`, [
        mockFeed({data: FIRST_PAGE, filter: {statuses: [status]}}),
      ]);

      await findRunLink(FIRST_PAGE_RUN_ID);
      const button = await screen.findByRole('button', TERMINATE_ALL_BUTTON);
      expect(button).toBeDisabled();
      expect(button).toHaveAccessibleDescription(DISABLED_REASON);
    },
  );

  it('closes the dialog when the filter changes under it', async () => {
    const user = userEvent.setup();
    const {history} = renderPage('/runs?q[]=status:FAILURE', [
      mockFeed({data: FIRST_PAGE, filter: {statuses: [RunStatus.FAILURE]}}),
      mockFeed({data: FIRST_PAGE, filter: {statuses: [RunStatus.QUEUED]}}),
    ]);

    act(() => history.push('/runs?q[]=status:QUEUED'));
    await openDialog(user);
    expect(await screen.findByRole('dialog')).toBeVisible();

    act(() => history.goBack());

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByRole('button', TERMINATE_ALL_BUTTON)).toBeDisabled();
  });

  it('refetches the feed when the dialog closes', async () => {
    const user = userEvent.setup();
    const {operations} = renderPage('/runs', [
      mockFeed({data: FIRST_PAGE}),
      mockTerminateBatch({statuses: TERMINABLE_STATUSES}),
    ]);

    await openDialog(user);
    await confirmTerminate(user, 'Terminate all');

    await waitFor(() =>
      expect(operations.filter((operation) => operation === 'RunsFeedQuery')).toHaveLength(2),
    );
  });

  it('is available on mobile', async () => {
    renderPage('/runs', [mockFeed({data: FIRST_PAGE})], true);

    await findRunLink(FIRST_PAGE_RUN_ID);
    expect(await screen.findByRole('button', TERMINATE_ALL_BUTTON)).toBeEnabled();
  });
});

describe('RunsPage selection', () => {
  const SELECT_RUNS_BUTTON = {name: 'Select runs'};
  const CLOSE_SELECTION_BUTTON = {name: 'Close and clear selection'};
  const SELECT_ALL_CHECKBOX = {name: 'Select all runs on this page'};
  const ACTIONS_BUTTON = {name: /^Actions/};

  const THREE_RUNS_PAGE = buildRunsFeedQueryResult([
    runSummary(FIRST_PAGE_RUN_ID),
    runSummary(SECOND_PAGE_RUN_ID),
    runSummary(THIRD_RUN_ID),
  ]);

  // The count's number and words are separate spans inside the bar's status region.
  const findSelectionCount = (text: string) =>
    screen.findByText(
      (_, element) => element?.getAttribute('role') === 'status' && element.textContent === text,
    );

  const findRunCheckbox = (id: string) =>
    screen.findByRole('checkbox', {name: `Select run ${shortenId(id)}`});

  const deleteMock = buildMutationMock<DeleteMutation, DeleteMutationVariables>({
    query: DELETE_MUTATION,
    variables: {runId: FIRST_PAGE_RUN_ID},
    data: {deletePipelineRun: buildDeletePipelineRunSuccess({runId: FIRST_PAGE_RUN_ID})},
  });

  const openDeleteDialog = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(await screen.findByRole('button', ACTIONS_BUTTON));
    await user.click(await screen.findByRole('menuitem', {name: /Delete 1 run$/}));
  };

  afterEach(() => {
    jest.useRealTimers();
  });

  it('opens the selection bar when a run is checked', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [mockFeed({data: THREE_RUNS_PAGE})]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));

    expect(await findSelectionCount('1 run selected')).toBeVisible();
    const runCheckbox = await findRunCheckbox(FIRST_PAGE_RUN_ID);
    expect(runCheckbox).toBeChecked();
    expect(runCheckbox).toHaveFocus();
    expect(await screen.findByRole('button', SELECT_RUNS_BUTTON)).toBeDisabled();
  });

  it('checks the runs between two checked runs on a shift-click', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [mockFeed({data: THREE_RUNS_PAGE})]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    await user.keyboard('{Shift>}');
    await user.click(await findRunCheckbox(THIRD_RUN_ID));
    await user.keyboard('{/Shift}');

    expect(await findSelectionCount('3 runs selected')).toBeVisible();
    expect(await findRunCheckbox(SECOND_PAGE_RUN_ID)).toBeChecked();
  });

  it('checks and unchecks every run on the page from the selection bar', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [mockFeed({data: THREE_RUNS_PAGE})]);

    await findRunCheckbox(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', SELECT_RUNS_BUTTON));
    await user.click(await screen.findByRole('checkbox', SELECT_ALL_CHECKBOX));

    expect(await findSelectionCount('3 runs selected')).toBeVisible();
    for (const id of [FIRST_PAGE_RUN_ID, SECOND_PAGE_RUN_ID, THIRD_RUN_ID]) {
      expect(await findRunCheckbox(id)).toBeChecked();
    }

    await user.click(await screen.findByRole('checkbox', SELECT_ALL_CHECKBOX));
    expect(await screen.findByText('Select runs')).toBeVisible();
  });

  it('clears the selection and closes the bar from its close button', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [mockFeed({data: THREE_RUNS_PAGE})]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    await user.click(await screen.findByRole('button', CLOSE_SELECTION_BUTTON));

    expect(screen.queryByRole('checkbox', SELECT_ALL_CHECKBOX)).not.toBeInTheDocument();
    expect(await findRunCheckbox(FIRST_PAGE_RUN_ID)).not.toBeChecked();
    expect(await screen.findByRole('button', SELECT_RUNS_BUTTON)).toBeEnabled();
  });

  it('opens an empty selection bar from Select runs and disables the button while the bar is open', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [mockFeed({data: THREE_RUNS_PAGE})]);

    await findRunCheckbox(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', SELECT_RUNS_BUTTON));

    expect(await screen.findByText('Select runs')).toBeVisible();
    expect(await screen.findByRole('button', ACTIONS_BUTTON)).toBeDisabled();
    expect(await screen.findByRole('button', SELECT_RUNS_BUTTON)).toBeDisabled();
  });

  // A new filter's first load empties the list, which drops the selection anyway; going back
  // to a cached filter does not.
  it('clears the selection when going back to a filter that returns a checked run', async () => {
    const user = userEvent.setup();
    const overlappingPage = buildRunsFeedQueryResult([
      runSummary(FIRST_PAGE_RUN_ID),
      runSummary(THIRD_RUN_ID),
    ]);
    const {history} = renderPage('/runs', [
      mockFeed({data: FIRST_PAGE}),
      mockFeed({data: overlappingPage, filter: {statuses: [RunStatus.FAILURE]}}),
    ]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    await applySearch('status:failure');
    await findRunLink(THIRD_RUN_ID);
    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    expect(await findSelectionCount('1 run selected')).toBeVisible();

    act(() => history.goBack());

    await waitFor(() =>
      expect(
        screen.queryByRole('link', {name: `Run ${shortenId(THIRD_RUN_ID)}`}),
      ).not.toBeInTheDocument(),
    );
    expect(await findRunCheckbox(FIRST_PAGE_RUN_ID)).not.toBeChecked();
    expect(await screen.findByText('Select runs')).toBeVisible();
  });

  it('clears the selection when a newer page returns a checked run', async () => {
    const user = userEvent.setup();
    renderPage('/runs', [
      mockFeed({
        data: buildRunsFeedQueryResult(
          [runSummary(FIRST_PAGE_RUN_ID), runSummary(SECOND_PAGE_RUN_ID)],
          {cursor: 'first', hasMore: true},
        ),
      }),
      mockFeed({
        data: buildRunsFeedQueryResult([runSummary(SECOND_PAGE_RUN_ID), runSummary(THIRD_RUN_ID)]),
        cursor: 'first',
      }),
    ]);

    await findRunLink(FIRST_PAGE_RUN_ID);
    await user.click(await screen.findByRole('button', OLDER_BUTTON));
    await findRunLink(THIRD_RUN_ID);
    await user.click(await findRunCheckbox(SECOND_PAGE_RUN_ID));
    expect(await findSelectionCount('1 run selected')).toBeVisible();

    await user.click(await screen.findByRole('button', NEWER_BUTTON));

    await findRunLink(FIRST_PAGE_RUN_ID);
    expect(await findRunCheckbox(SECOND_PAGE_RUN_ID)).not.toBeChecked();
    expect(await screen.findByText('Select runs')).toBeVisible();
  });

  it('clears the selection and refetches after deleting, keeping the result', async () => {
    const user = userEvent.setup();
    const {operations} = renderPage('/runs', [mockFeed({data: FIRST_PAGE}), deleteMock]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    await openDeleteDialog(user);
    await user.click(await screen.findByRole('button', {name: 'Yes, delete 1 run'}));

    expect(await screen.findByText('Successfully deleted 1 run.')).toBeVisible();
    expect(await screen.findByText('Select runs')).toBeVisible();
    await waitFor(() =>
      expect(operations.filter((operation) => operation === 'RunsFeedQuery')).toHaveLength(2),
    );
  });

  it('keeps the selection when polling returns the checked run', async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    renderPage('/runs', [
      mockFeed({
        data: buildRunsFeedQueryResult([
          runSummary(FIRST_PAGE_RUN_ID),
          runSummary(SECOND_PAGE_RUN_ID),
        ]),
        maxUsageCount: 1,
      }),
      mockFeed({data: THREE_RUNS_PAGE}),
    ]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    expect(await findSelectionCount('1 run selected')).toBeVisible();

    act(() => jest.advanceTimersByTime(15_000));

    await findRunLink(THIRD_RUN_ID);
    expect(await findSelectionCount('1 run selected')).toBeVisible();
    expect(await findRunCheckbox(FIRST_PAGE_RUN_ID)).toBeChecked();
  });

  it('keeps an open dialog when polling removes the checked run', async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    renderPage('/runs', [
      mockFeed({
        data: buildRunsFeedQueryResult([
          runSummary(FIRST_PAGE_RUN_ID),
          runSummary(SECOND_PAGE_RUN_ID),
        ]),
        maxUsageCount: 1,
      }),
      mockFeed({data: buildRunsFeedQueryResult([runSummary(SECOND_PAGE_RUN_ID)])}),
    ]);

    await user.click(await findRunCheckbox(FIRST_PAGE_RUN_ID));
    await openDeleteDialog(user);
    expect(await screen.findByText('1 run will be deleted.')).toBeVisible();

    act(() => jest.advanceTimersByTime(15_000));

    await waitFor(() =>
      expect(
        screen.queryByRole('link', {name: `Run ${shortenId(FIRST_PAGE_RUN_ID)}`}),
      ).not.toBeInTheDocument(),
    );
    expect(await screen.findByText('Select runs')).toBeVisible();
    expect(await screen.findByText('1 run will be deleted.')).toBeVisible();
  });

  it('has no selection controls on mobile', async () => {
    renderPage('/runs', [mockFeed({data: FIRST_PAGE})], true);

    await findRunLink(FIRST_PAGE_RUN_ID);
    expect(screen.queryByRole('checkbox', {name: /^Select run/})).not.toBeInTheDocument();
    expect(screen.queryByRole('button', SELECT_RUNS_BUTTON)).not.toBeInTheDocument();
  });
});
