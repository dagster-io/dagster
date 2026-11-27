import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Toaster} from '@dagster-io/ui-components';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {globalAssetGraphPathForAssets} from '../../../assets/globalAssetGraphPathToString';
import {
  buildAssetCheckhandle,
  buildAssetKey,
  buildExecutionPlan,
  buildPipeline,
  buildPythonError,
  buildRepository,
  buildRepositoryLocation,
  buildRun,
  buildWorkspaceLocationEntry,
} from '../../../graphql/builders';
import {AssetKeyInput, ReexecutionStrategy, RunStatus} from '../../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../../launchpad/uiExecutionTags';
import {buildQueryMock} from '../../../testing/mocking';
import {testId} from '../../../testing/testId';
import {WorkspaceProvider} from '../../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {RunsQueryRefetchContext} from '../../RunUtils';
import {buildLaunchPipelineReexecutionSuccessMock} from '../../__fixtures__/Reexecution.fixtures';
import {RunActionsCell} from '../RunActionsCell';
import {RUN_ACTIONS_MENU_QUERY} from '../RunActionsMenuQuery';
import {runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {
  RunActionsMenuQuery,
  RunActionsMenuQueryVariables,
} from '../types/RunActionsMenuQuery.types';
import {RunSummaryFragment} from '../types/RunsFeedFragments.types';

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const JOB_NAME = 'daily_etl';
const SNAPSHOT_ID = 'snapshot-id';
const LIST_PATH = '/runs';

const salesDaily = buildAssetKey({path: ['sales', 'daily']});
const salesHourly = buildAssetKey({path: ['sales', 'hourly']});
const freshnessCheck = buildAssetCheckhandle({assetKey: salesDaily, name: 'freshness'});

const RUN_CONFIG_YAML = 'ops:\n  load_sales:\n    config:\n      limit: 10\n';

const buildMenuRun = (overrides: Partial<RunSummaryFragment> = {}) =>
  runEntry({
    id: RUN_ID,
    jobName: JOB_NAME,
    pipelineSnapshotId: SNAPSHOT_ID,
    hasReExecutePermission: true,
    hasTerminatePermission: true,
    hasDeletePermission: true,
    hasRunMetricsEnabled: false,
    ...overrides,
  });

type MenuDetails = {
  runConfigYaml?: string;
  assetSelection?: AssetKeyInput[] | null;
  assetCheckSelection?: AssetKeyInput[] | null;
  planAssetKeys?: AssetKeyInput[];
  parentPipelineSnapshotId?: string | null;
};

const buildMenuQueryMock = (
  {
    runConfigYaml = '{}\n',
    assetSelection = null,
    assetCheckSelection = null,
    planAssetKeys = [],
    parentPipelineSnapshotId = null,
  }: MenuDetails = {},
  options: Partial<MockedResponse> = {},
) =>
  buildQueryMock<RunActionsMenuQuery, RunActionsMenuQueryVariables>({
    query: RUN_ACTIONS_MENU_QUERY,
    variables: {runId: RUN_ID},
    data: {
      runOrError: buildRun({
        id: RUN_ID,
        parentPipelineSnapshotId,
        runConfigYaml,
        assetSelection: assetSelection?.map((key) => buildAssetKey(key)) ?? null,
        assetCheckSelection:
          assetCheckSelection?.map((assetKey) =>
            buildAssetCheckhandle({assetKey: buildAssetKey(assetKey), name: 'freshness'}),
          ) ?? null,
        executionPlan: buildExecutionPlan({
          assetKeys: planAssetKeys.map((key) => buildAssetKey(key)),
        }),
      }),
    },
    ...options,
  });

const workspaceMocks = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    id: 'my_location',
    name: 'my_location',
    locationOrLoadError: buildRepositoryLocation({
      id: 'my_location',
      name: 'my_location',
      repositories: [
        buildRepository({
          id: 'my_repo',
          name: 'my_repo',
          pipelines: [
            buildPipeline({
              id: JOB_NAME,
              name: JOB_NAME,
              isJob: true,
              pipelineSnapshotId: SNAPSHOT_ID,
            }),
          ],
        }),
      ],
    }),
  }),
]);

const CurrentPath = () => {
  const {pathname} = useLocation();
  return <div data-testid={testId('path')}>{pathname}</div>;
};

const renderActionsCell = (
  run: ReturnType<typeof buildMenuRun>,
  mocks: MockedResponse[] = [buildMenuQueryMock()],
) => {
  const refetch = jest.fn();
  const onOpenRunDialog = jest.fn();
  render(
    <MemoryRouter initialEntries={[LIST_PATH]}>
      <MockedProvider mocks={[...workspaceMocks, ...mocks]}>
        <WorkspaceProvider>
          <RunsQueryRefetchContext.Provider value={{refetch}}>
            <RunActionsCell run={run} onOpenRunDialog={onOpenRunDialog} />
          </RunsQueryRefetchContext.Provider>
        </WorkspaceProvider>
      </MockedProvider>
      <CurrentPath />
      <Toaster />
    </MemoryRouter>,
  );
  return {refetch, onOpenRunDialog};
};

const itemName = (text: string) => new RegExp(`${text}$`);

const findItem = (text: string) => screen.findByRole('menuitem', {name: itemName(text)});

const getItem = (text: string) => screen.getByRole('menuitem', {name: itemName(text)});

const queryItem = (text: string) => screen.queryByRole('menuitem', {name: itemName(text)});

const getQueryDependentItems = () =>
  ['Open in Launchpad', 'View asset selection', 'View configuration'].filter(
    (text) => queryItem(text) !== null,
  );

const findMenuButton = () => screen.findByRole('button', {name: 'Run actions'});

const openMenu = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.click(await findMenuButton());
  return screen.findByRole('menu');
};

const waitForMenuQuery = async () => {
  await waitFor(() => expect(screen.getByRole('status')).toBeEmptyDOMElement());
};

describe('RunActionsCell', () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  it.each([
    {
      name: 'a queued run',
      run: buildMenuRun({runStatus: RunStatus.QUEUED, startTime: null, endTime: null}),
      details: {},
      present: ['View queue criteria', 'Terminate'],
      absent: [],
    },
    {
      name: 'a run with an explicit asset selection',
      run: buildMenuRun({assetSelectionPreview: [salesDaily], assetSelectionCount: 1}),
      details: {assetSelection: [salesDaily]},
      present: ['View asset selection'],
      absent: ['Open in Launchpad'],
    },
    {
      name: 'a run with no explicit selection whose plan has assets',
      run: buildMenuRun(),
      details: {planAssetKeys: [salesDaily]},
      present: ['View asset selection'],
      absent: ['Open in Launchpad'],
    },
    {
      name: 'a succeeded run with no explicit selection',
      run: buildMenuRun(),
      details: {},
      present: ['Open in Launchpad', 'View snapshot'],
      absent: ['View asset selection', 'View configuration', 'View queue criteria', 'Terminate'],
    },
    {
      name: 'a run with only a check selection',
      run: buildMenuRun({
        assetSelectionPreview: null,
        assetCheckSelectionPreview: [freshnessCheck],
        assetCheckSelectionCount: 1,
      }),
      details: {assetCheckSelection: [salesDaily]},
      present: ['View asset selection'],
      absent: ['Open in Launchpad'],
    },
    {
      name: 'a run with config',
      run: buildMenuRun(),
      details: {runConfigYaml: RUN_CONFIG_YAML},
      present: ['View configuration'],
      absent: [],
    },
    {
      name: 'a hidden asset job run',
      run: buildMenuRun({jobName: '__ASSET_JOB_0'}),
      details: {},
      present: [],
      absent: ['Open in Launchpad', 'View snapshot'],
    },
    {
      name: 'an external run',
      run: buildMenuRun({tags: [tag('dagster/external_job_source', 'airflow')]}),
      details: {},
      present: [],
      absent: ['Open in Launchpad'],
    },
  ])('shows the items that apply to $name', async ({run, details, present, absent}) => {
    const user = userEvent.setup();
    renderActionsCell(run, [buildMenuQueryMock(details)]);

    await openMenu(user);
    await waitForMenuQuery();

    for (const text of present) {
      expect(await findItem(text)).toBeVisible();
    }
    for (const text of absent) {
      expect(queryItem(text)).not.toBeInTheDocument();
    }
  });

  it('copies the full run ID with a toast', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun());

    await openMenu(user);
    await user.click(await findItem('Copy full run ID'));

    expect(await screen.findByText('Run ID copied')).toBeVisible();
    expect(await navigator.clipboard.readText()).toBe(RUN_ID);
  });

  it('links Open in Launchpad to the job in its code location', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun());

    await openMenu(user);

    await waitFor(async () =>
      expect(await findItem('Open in Launchpad')).toHaveAttribute(
        'href',
        `/locations/my_repo@my_location/jobs/${JOB_NAME}/playground/setup-from-run/${RUN_ID}`,
      ),
    );
  });

  it('disables actions the user has no permission for', async () => {
    const user = userEvent.setup();
    renderActionsCell(
      buildMenuRun({
        runStatus: RunStatus.STARTED,
        endTime: null,
        hasReExecutePermission: false,
        hasTerminatePermission: false,
        hasDeletePermission: false,
      }),
    );

    await openMenu(user);
    await waitForMenuQuery();

    for (const text of ['Re-execute', 'Terminate', 'Delete']) {
      expect(await findItem(text)).toBeDisabled();
    }

    await user.hover(await findItem('Delete'));
    expect((await screen.findAllByText('Insufficient permissions')).length).toBeGreaterThan(0);
  });

  it('re-executes with a toast instead of opening the new run', async () => {
    const user = userEvent.setup();
    const {refetch} = renderActionsCell(buildMenuRun(), [
      buildMenuQueryMock(),
      buildLaunchPipelineReexecutionSuccessMock({
        parentRunId: RUN_ID,
        strategy: ReexecutionStrategy.ALL_STEPS,
        extraTags: UI_EXECUTION_TAGS,
      }),
    ]);

    await openMenu(user);
    await waitFor(async () => expect(await findItem('Re-execute')).toBeEnabled());
    await user.click(await findItem('Re-execute'));

    expect(await screen.findByText(/Launched run/)).toBeVisible();
    expect(refetch).toHaveBeenCalled();
    expect(screen.getByTestId('path').textContent).toBe(LIST_PATH);
  });

  it('requests the config dialog and closes the menu when View configuration is chosen', async () => {
    const user = userEvent.setup();
    const run = buildMenuRun();
    const {onOpenRunDialog} = renderActionsCell(run, [
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}),
    ]);

    await openMenu(user);
    await user.click(await findItem('View configuration'));

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(onOpenRunDialog).toHaveBeenCalledWith(
      {kind: 'config', run, runConfigYaml: RUN_CONFIG_YAML, isJob: true},
      await findMenuButton(),
    );
  });

  it('shows cached items at once when the menu reopens after a dialog is requested', async () => {
    const user = userEvent.setup();
    const run = buildMenuRun();
    // The reopen refetches slowly, so the items can only come from the cache.
    const {onOpenRunDialog} = renderActionsCell(run, [
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}),
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}, {delay: 10000}),
    ]);

    await openMenu(user);
    expect(await findItem('View configuration')).toBeVisible();
    await user.click(await findItem('Delete'));

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(onOpenRunDialog).toHaveBeenCalledWith({kind: 'delete', run}, await findMenuButton());

    await openMenu(user);
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(getItem('View configuration')).toBeVisible();
    expect(getItem('Re-execute')).toBeEnabled();
  });

  it('hides View all tags for a run without tags', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun({tags: []}), [buildMenuQueryMock()]);

    await openMenu(user);

    expect(await findItem('Copy full run ID')).toBeVisible();
    expect(queryItem('View all tags')).not.toBeInTheDocument();
  });

  it('orders the items for a queued job run with config', async () => {
    const user = userEvent.setup();
    renderActionsCell(
      buildMenuRun({
        runStatus: RunStatus.QUEUED,
        startTime: null,
        endTime: null,
        tags: [tag('team', 'data')],
      }),
      [buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML})],
    );

    await openMenu(user);
    await waitForMenuQuery();

    const items = await screen.findAllByRole('menuitem');
    expect(items.map((item) => item.textContent)).toEqual([
      'Copy full run ID',
      'View all tags',
      'Open in Launchpad',
      'View configuration',
      'View snapshot',
      'View queue criteria',
      'Re-execute',
      'Terminate',
      'Delete',
    ]);
  });

  it('moves focus into a menu opened with a click', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun());

    await openMenu(user);

    await waitFor(async () => expect(await findItem('Copy full run ID')).toHaveFocus());
  });

  it('shows only the skeleton until the menu query returns', async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    renderActionsCell(buildMenuRun(), [
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}, {delay: 10000}),
    ]);

    await openMenu(user);
    expect(screen.getByRole('status')).toHaveTextContent('Loading');
    expect(await findItem('Re-execute')).toBeDisabled();
    expect(getQueryDependentItems()).toEqual([]);

    act(() => jest.advanceTimersByTime(10000));
    await waitForMenuQuery();
    expect(getQueryDependentItems()).toEqual(['Open in Launchpad', 'View configuration']);
  });

  it('drops query-dependent items and keeps Re-execute when the menu query fails', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun(), [
      {
        request: {query: RUN_ACTIONS_MENU_QUERY, variables: {runId: RUN_ID}},
        error: new Error('Network error'),
      },
    ]);

    await openMenu(user);
    await waitForMenuQuery();

    expect(getQueryDependentItems()).toEqual([]);
    await waitFor(async () => expect(await findItem('Re-execute')).toBeEnabled());
  });

  it.each<{name: string; failure: MockedResponse}>([
    {
      name: 'a network error',
      failure: {
        request: {query: RUN_ACTIONS_MENU_QUERY, variables: {runId: RUN_ID}},
        error: new Error('Network error'),
      },
    },
    {
      name: 'an error result',
      failure: buildQueryMock<RunActionsMenuQuery, RunActionsMenuQueryVariables>({
        query: RUN_ACTIONS_MENU_QUERY,
        variables: {runId: RUN_ID},
        data: {runOrError: buildPythonError()},
      }),
    },
  ])('retries the menu query when the menu reopens after $name', async ({failure}) => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun(), [
      failure,
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}),
    ]);

    await openMenu(user);
    await waitForMenuQuery();
    expect(queryItem('View configuration')).not.toBeInTheDocument();

    await user.keyboard('{Escape}');
    await openMenu(user);

    expect(await findItem('View configuration')).toBeVisible();
  });

  it.each([
    {
      name: "includes a check's parent asset",
      run: buildMenuRun({
        assetSelectionPreview: null,
        assetCheckSelectionPreview: [freshnessCheck],
        assetCheckSelectionCount: 1,
      }),
      details: {assetCheckSelection: [salesDaily]},
      expectedKeys: [salesDaily],
    },
    {
      name: 'collapses an asset that is also a check parent',
      run: buildMenuRun({
        assetSelectionPreview: [salesDaily, salesHourly],
        assetSelectionCount: 2,
        assetCheckSelectionPreview: [freshnessCheck],
        assetCheckSelectionCount: 1,
      }),
      details: {assetSelection: [salesDaily, salesHourly], assetCheckSelection: [salesDaily]},
      expectedKeys: [salesDaily, salesHourly],
    },
    {
      name: 'uses the plan for a run with no explicit selection',
      run: buildMenuRun(),
      details: {planAssetKeys: [salesHourly]},
      expectedKeys: [salesHourly],
    },
  ])(
    'links View asset selection to the asset graph: $name',
    async ({run, details, expectedKeys}) => {
      const user = userEvent.setup();
      renderActionsCell(run, [buildMenuQueryMock(details)]);

      await openMenu(user);

      // The router encodes the path differently from the helper, so compare them decoded.
      const href = (await findItem('View asset selection')).getAttribute('href') ?? '';
      expect(decodeURIComponent(href)).toBe(
        decodeURIComponent(globalAssetGraphPathForAssets(expectedKeys.map(({path}) => ({path})))),
      );
    },
  );

  it('moves focus into a menu opened from the keyboard and back to the button on Escape', async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    renderActionsCell(buildMenuRun(), [
      buildMenuQueryMock({runConfigYaml: RUN_CONFIG_YAML}, {delay: 10000}),
    ]);

    await user.tab();
    expect(await findMenuButton()).toHaveFocus();
    await user.keyboard('{Enter}');

    await waitFor(async () => expect(await findItem('Copy full run ID')).toHaveFocus());

    // Move off the item that autofocus picks, so refocusing on load would show up.
    const snapshotItem = await findItem('View snapshot');
    act(() => snapshotItem.focus());

    act(() => jest.advanceTimersByTime(10000));
    expect(await findItem('View configuration')).toBeVisible();
    expect(snapshotItem).toHaveFocus();

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(await findMenuButton()).toHaveFocus();
  });
});
