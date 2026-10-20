import {MockLink, MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {ApolloLink} from '../../apollo-client';
import {ReexecutionStrategy} from '../../graphql/types';
import {UI_EXECUTION_TAGS} from '../../launchpad/uiExecutionTags';
import {testId} from '../../testing/testId';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {RunActionsMenu} from '../RunActionsMenu';
import {buildLaunchPipelineReexecutionSuccessMock} from '../__fixtures__/Reexecution.fixtures';
import {
  buildMockRootWorkspaceQuery,
  buildPipelineEnvironmentQuery,
  buildRunActionsMenuFragment,
} from '../__fixtures__/RunActionsMenu.fixtures';

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
