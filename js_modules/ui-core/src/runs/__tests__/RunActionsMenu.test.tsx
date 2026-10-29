import {MockLink, MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {ApolloLink} from '../../apollo-client';
import {
  buildDeletePipelineRunSuccess,
  buildRun,
  buildTerminateRunSuccess,
  buildTerminateRunsResult,
} from '../../graphql/builders';
import {ReexecutionStrategy, RunStatus, TerminateRunPolicy} from '../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../launchpad/uiExecutionTags';
import {buildMutationMock} from '../../testing/mocking';
import {testId} from '../../testing/testId';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {RunActionsMenu, RunBulkActionsMenu} from '../RunActionsMenu';
import {DELETE_MUTATION, TERMINATE_MUTATION} from '../RunUtils';
import {buildLaunchPipelineReexecutionSuccessMock} from '../__fixtures__/Reexecution.fixtures';
import {
  buildMockRootWorkspaceQuery,
  buildPipelineEnvironmentQuery,
  buildRunActionsMenuFragment,
} from '../__fixtures__/RunActionsMenu.fixtures';
import {
  DeleteMutation,
  DeleteMutationVariables,
  TerminateMutation,
  TerminateMutationVariables,
} from '../types/RunUtils.types';

const CurrentPath = () => {
  const {pathname} = useLocation();
  return <div data-testid={testId('path')}>{pathname}</div>;
};

describe('RunActionsMenu', () => {
  it('closes the menu as soon as Re-execute is clicked and launches one run', async () => {
    const user = userEvent.setup();
    const run = buildRunActionsMenuFragment({hasReExecutePermission: true});
    // Count launch requests as they are sent, since the mock only responds after a delay.
    const launches = jest.fn();
    const countLink = new ApolloLink((operation, forward) => {
      if (operation.operationName === 'LaunchPipelineReexecution') {
        launches();
      }
      return forward(operation);
    });
    const mockLink = new MockLink([
      ...buildMockRootWorkspaceQuery(),
      buildPipelineEnvironmentQuery({hasReExecutePermission: true}),
      {
        ...buildLaunchPipelineReexecutionSuccessMock({
          parentRunId: run.id,
          strategy: ReexecutionStrategy.ALL_STEPS,
          extraTags: UI_EXECUTION_TAGS,
        }),
        maxUsageCount: 2,
        delay: 100,
      },
    ]);
    render(
      <MockedProvider link={ApolloLink.from([countLink, mockLink])}>
        <MemoryRouter>
          <WorkspaceProvider>
            <RunActionsMenu run={run} />
            <CurrentPath />
          </WorkspaceProvider>
        </MemoryRouter>
      </MockedProvider>,
    );

    await user.click(await screen.findByRole('button'));
    const reexecute = await screen.findByRole('menuitem', {name: /re\-execute/i});
    await waitFor(() => expect(reexecute).toBeEnabled());

    await user.click(reexecute);

    // The menu is gone before the launch completes, so there is nothing left to click twice.
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(screen.getByTestId('path').textContent).toBe('/');
    expect(launches).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(screen.getByTestId('path').textContent).toBe('/runs/1234');
    });
    expect(launches).toHaveBeenCalledTimes(1);
  });

  describe('Permissions', () => {
    it('renders menu when open', async () => {
      const user = userEvent.setup();
      render(
        <MockedProvider
          mocks={[
            ...buildMockRootWorkspaceQuery(),
            buildPipelineEnvironmentQuery({hasReExecutePermission: true}),
          ]}
        >
          <MemoryRouter>
            <WorkspaceProvider>
              <RunActionsMenu run={buildRunActionsMenuFragment({hasReExecutePermission: true})} />
            </WorkspaceProvider>
          </MemoryRouter>
        </MockedProvider>,
      );

      const button = await screen.findByRole('button');
      expect(button).toBeVisible();

      await user.click(button);

      expect(await screen.findByRole('menuitem', {name: /view configuration/i})).toBeVisible();
      expect(await screen.findByRole('menuitem', {name: /open in launchpad/i})).toBeVisible();
      expect(await screen.findByRole('menuitem', {name: /re\-execute/i})).toBeVisible();
      expect(await screen.findByRole('menuitem', {name: /download debug file/i})).toBeVisible();
      expect(await screen.findByRole('menuitem', {name: /delete/i})).toBeVisible();
    });

    it('disables re-execution if no permission', async () => {
      const user = userEvent.setup();
      render(
        <MockedProvider
          mocks={[
            ...buildMockRootWorkspaceQuery(),
            buildPipelineEnvironmentQuery({hasReExecutePermission: false}),
          ]}
        >
          <MemoryRouter>
            <WorkspaceProvider>
              <RunActionsMenu run={buildRunActionsMenuFragment({hasReExecutePermission: false})} />
            </WorkspaceProvider>
          </MemoryRouter>
        </MockedProvider>,
      );

      const button = await screen.findByRole('button');
      expect(button).toBeVisible();

      await user.click(button);

      const reExecutionButton = await screen.findByRole('menuitem', {
        name: /re\-execute/i,
      });

      // Blueprint doesn't actually set `disabled` on the button element.
      expect(reExecutionButton).toBeDisabled();
    });

    it('does not offer to terminate instead of deleting without terminate permission', async () => {
      const user = userEvent.setup();
      render(
        <MockedProvider
          mocks={[
            ...buildMockRootWorkspaceQuery(),
            buildPipelineEnvironmentQuery({hasReExecutePermission: true}),
          ]}
        >
          <MemoryRouter>
            <WorkspaceProvider>
              <RunActionsMenu
                run={{
                  ...buildRunActionsMenuFragment({hasReExecutePermission: true}),
                  hasTerminatePermission: false,
                }}
              />
            </WorkspaceProvider>
          </MemoryRouter>
        </MockedProvider>,
      );

      await user.click(await screen.findByRole('button'));
      await user.click(await screen.findByRole('menuitem', {name: /delete/i}));

      expect(await screen.findByText('1 run will be deleted.')).toBeVisible();
      expect(screen.queryByRole('button', {name: /instead/})).not.toBeInTheDocument();
    });
  });
});

type BulkRun = ReturnType<typeof buildRunActionsMenuFragment>;

const RUNNING = {status: RunStatus.STARTED, endTime: null};

const buildBulkRun = (overrides: Partial<BulkRun>) => {
  return {...buildRunActionsMenuFragment({hasReExecutePermission: false}), ...overrides};
};

const buildDeleteMock = (runId: string) =>
  buildMutationMock<DeleteMutation, DeleteMutationVariables>({
    query: DELETE_MUTATION,
    variables: {runId},
    data: {deletePipelineRun: buildDeletePipelineRunSuccess({runId})},
  });

const buildTerminateMock = (runId: string) =>
  buildMutationMock<TerminateMutation, TerminateMutationVariables>({
    query: TERMINATE_MUTATION,
    variables: {runIds: [runId], terminatePolicy: TerminateRunPolicy.SAFE_TERMINATE},
    data: {
      terminateRuns: buildTerminateRunsResult({
        terminateRunResults: [
          buildTerminateRunSuccess({run: buildRun({id: runId, canTerminate: true})}),
        ],
      }),
    },
  });

const renderBulkMenu = (
  selected: BulkRun[],
  mocks: React.ComponentProps<typeof MockedProvider>['mocks'] = [],
) => {
  const buildBulkMenu = (runs: BulkRun[]) => (
    <MockedProvider mocks={mocks}>
      <MemoryRouter>
        <RunBulkActionsMenu selected={runs} clearSelection={() => {}} />
      </MemoryRouter>
    </MockedProvider>
  );
  const {rerender} = render(buildBulkMenu(selected));
  return {
    rerenderSelected: (runs: BulkRun[]) => rerender(buildBulkMenu(runs)),
  };
};

describe('RunBulkActionsMenu', () => {
  it('only deletes runs the user can delete', async () => {
    const user = userEvent.setup();
    renderBulkMenu(
      [buildBulkRun({id: 'run-a'}), buildBulkRun({id: 'run-b', hasDeletePermission: false})],
      [buildDeleteMock('run-a')],
    );

    await user.click(await screen.findByRole('button', {name: /Actions/}));
    await user.click(await screen.findByRole('menuitem', {name: /Delete 1 run$/}));
    await user.click(await screen.findByRole('button', {name: 'Yes, delete 1 run'}));

    expect(await screen.findByText('Successfully deleted 1 run.')).toBeVisible();
  });

  it('shows actions the user cannot take as disabled with a permission reason', async () => {
    const user = userEvent.setup();
    const noPermissions = {hasDeletePermission: false, hasTerminatePermission: false};
    renderBulkMenu([
      buildBulkRun({id: 'run-a', ...RUNNING, ...noPermissions}),
      buildBulkRun({id: 'run-b', ...noPermissions}),
    ]);

    await user.click(await screen.findByRole('button', {name: /Actions/}));

    const terminateItem = await screen.findByRole('menuitem', {name: /Terminate 1 run$/});
    expect(terminateItem).toBeDisabled();
    expect(await screen.findByRole('menuitem', {name: /Delete 2 runs$/})).toBeDisabled();
    expect(await screen.findByRole('menuitem', {name: /Re-execute 1 run$/})).toBeDisabled();

    await user.hover(terminateItem);
    expect(await screen.findByRole('tooltip', {name: 'Insufficient permissions'})).toBeVisible();
  });

  it('hides actions that do not apply to the selected runs', async () => {
    const user = userEvent.setup();
    renderBulkMenu([buildBulkRun({hasReExecutePermission: true})]);

    await user.click(await screen.findByRole('button', {name: /Actions/}));

    expect(await screen.findByRole('menuitem', {name: /Delete 1 run$/})).toBeVisible();
    expect(await screen.findByRole('menuitem', {name: /Re-execute 1 run$/})).toBeVisible();
    expect(screen.queryByRole('menuitem', {name: /Terminate/})).not.toBeInTheDocument();
    expect(screen.queryByRole('menuitem', {name: /from failure/})).not.toBeInTheDocument();
  });

  it('terminate instead covers only the runs the delete dialog counted', async () => {
    const user = userEvent.setup();
    renderBulkMenu(
      [
        buildBulkRun({id: 'run-a', ...RUNNING}),
        buildBulkRun({id: 'run-b', hasDeletePermission: false, ...RUNNING}),
      ],
      [buildTerminateMock('run-a')],
    );

    await user.click(await screen.findByRole('button', {name: /Actions/}));
    await user.click(await screen.findByRole('menuitem', {name: /Delete 1 run$/}));
    await user.click(await screen.findByRole('button', {name: 'Terminate 1 run instead'}));
    await user.click(await screen.findByRole('button', {name: 'Terminate 1 run'}));

    expect(await screen.findByText('Successfully requested termination for 1 run.')).toBeVisible();
  });

  it('terminate instead keeps the runs the delete dialog counted after the list refreshes', async () => {
    const user = userEvent.setup();
    const {rerenderSelected} = renderBulkMenu(
      [
        buildBulkRun({id: 'run-a', ...RUNNING}),
        buildBulkRun({id: 'run-b', hasTerminatePermission: false, ...RUNNING}),
      ],
      [buildTerminateMock('run-a')],
    );

    await user.click(await screen.findByRole('button', {name: /Actions/}));
    await user.click(await screen.findByRole('menuitem', {name: /Delete 2 runs$/}));
    expect(await screen.findByRole('button', {name: 'Terminate 1 run instead'})).toBeVisible();

    rerenderSelected([
      buildBulkRun({id: 'run-a', status: RunStatus.SUCCESS, canTerminate: false}),
      buildBulkRun({id: 'run-b', ...RUNNING}),
    ]);

    await user.click(await screen.findByRole('button', {name: 'Terminate 1 run instead'}));
    await user.click(await screen.findByRole('button', {name: 'Terminate 1 run'}));

    expect(await screen.findByText('Successfully requested termination for 1 run.')).toBeVisible();
  });

  it('does not offer to terminate instead of deleting without terminate permission', async () => {
    const user = userEvent.setup();
    renderBulkMenu([buildBulkRun({...RUNNING, hasTerminatePermission: false})]);

    await user.click(await screen.findByRole('button', {name: /Actions/}));
    await user.click(await screen.findByRole('menuitem', {name: /Delete 1 run$/}));

    expect(await screen.findByText('1 run will be deleted.')).toBeVisible();
    expect(screen.queryByRole('button', {name: /instead/})).not.toBeInTheDocument();
  });
});
