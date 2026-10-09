import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Toaster} from '@dagster-io/ui-components';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {
  buildAssetKey,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../../graphql/builders';
import {ReexecutionStrategy, RunStatus} from '../../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../../launchpad/uiExecutionTags';
import {testId} from '../../../testing/testId';
import {WorkspaceProvider} from '../../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {RunsQueryRefetchContext} from '../../RunUtils';
import {buildLaunchPipelineReexecutionSuccessMock} from '../../__fixtures__/Reexecution.fixtures';
import {RunActionsCell} from '../RunActionsCell';
import {runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {RunSummaryFragment} from '../types/RunsFeedFragments.types';

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const JOB_NAME = 'daily_etl';
const SNAPSHOT_ID = 'snapshot-id';
const LIST_PATH = '/runs';

const salesDaily = buildAssetKey({path: ['sales', 'daily']});

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

const renderActionsCell = (run: ReturnType<typeof buildMenuRun>, mocks: MockedResponse[] = []) => {
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

const queryItem = (text: string) => screen.queryByRole('menuitem', {name: itemName(text)});

const findMenuButton = () => screen.findByRole('button', {name: 'Run actions'});

const openMenu = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.click(await findMenuButton());
  return screen.findByRole('menu');
};

describe('RunActionsCell', () => {
  it.each([
    {
      name: 'a queued run',
      run: buildMenuRun({runStatus: RunStatus.QUEUED, startTime: null, endTime: null}),
      present: ['View queue criteria', 'Terminate'],
      absent: [],
    },
    {
      name: 'a run with an explicit asset selection',
      run: buildMenuRun({assetSelectionPreview: [salesDaily], assetSelectionCount: 1}),
      present: [],
      absent: ['Open in Launchpad'],
    },
    {
      name: 'a succeeded run with no explicit selection',
      run: buildMenuRun(),
      present: ['Open in Launchpad', 'View snapshot'],
      absent: ['View queue criteria', 'Terminate'],
    },
    {
      name: 'a hidden asset job run',
      run: buildMenuRun({jobName: '__ASSET_JOB_0'}),
      present: [],
      absent: ['Open in Launchpad', 'View snapshot'],
    },
    {
      name: 'an external run',
      run: buildMenuRun({tags: [tag('dagster/external_job_source', 'airflow')]}),
      present: [],
      absent: ['Open in Launchpad'],
    },
  ])('shows the items that apply to $name', async ({run, present, absent}) => {
    const user = userEvent.setup();
    renderActionsCell(run);

    await openMenu(user);

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

    for (const text of ['Re-execute', 'Terminate', 'Delete']) {
      expect(await findItem(text)).toBeDisabled();
    }

    await user.hover(await findItem('Delete'));
    expect((await screen.findAllByText('Insufficient permissions')).length).toBeGreaterThan(0);
  });

  it('re-executes with a toast instead of opening the new run', async () => {
    const user = userEvent.setup();
    const {refetch} = renderActionsCell(buildMenuRun(), [
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

  it('requests the dialog and closes the menu when Delete is chosen', async () => {
    const user = userEvent.setup();
    const run = buildMenuRun();
    const {onOpenRunDialog} = renderActionsCell(run);

    await openMenu(user);
    await user.click(await findItem('Delete'));

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(onOpenRunDialog).toHaveBeenCalledWith({kind: 'delete', run}, await findMenuButton());
  });

  it('moves focus into a menu opened with a click', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun());

    await openMenu(user);

    await waitFor(async () => expect(await findItem('Copy full run ID')).toHaveFocus());
  });

  it('moves focus into a menu opened from the keyboard and back to the button on Escape', async () => {
    const user = userEvent.setup();
    renderActionsCell(buildMenuRun());

    await user.tab();
    expect(await findMenuButton()).toHaveFocus();
    await user.keyboard('{Enter}');

    const copyItem = await findItem('Copy full run ID');
    await waitFor(() => expect(copyItem).toHaveFocus());

    expect(await findItem('Open in Launchpad')).toBeVisible();
    expect(copyItem).toHaveFocus();

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(await findMenuButton()).toHaveFocus();
  });
});
