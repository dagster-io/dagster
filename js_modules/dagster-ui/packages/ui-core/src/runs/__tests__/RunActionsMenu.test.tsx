import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {RunActionsMenu} from '../RunActionsMenu';
import {
  buildMockRootWorkspaceQuery,
  buildPipelineEnvironmentQuery,
  buildRunActionsMenuFragment,
} from '../__fixtures__/RunActionsMenu.fixtures';

describe('RunActionsMenu', () => {
  describe('Permissions', () => {
    it('renders menu when open', async () => {
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

      await userEvent.click(button);

      expect(screen.queryByRole('menuitem', {name: /view configuration/i})).toBeVisible();
      expect(screen.queryByRole('link', {name: /open in launchpad/i})).toBeVisible();
      expect(screen.queryByRole('menuitem', {name: /re\-execute/i})).toBeVisible();
      expect(screen.queryByRole('menuitem', {name: /download debug file/i})).toBeVisible();
      expect(screen.queryByRole('menuitem', {name: /delete/i})).toBeVisible();
    });

    it('disables re-execution if no permission', async () => {
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

      await userEvent.click(button);

      const reExecutionButton = await screen.findByRole('menuitem', {
        name: /re\-execute/i,
      });

      // Blueprint doesn't actually set `disabled` on the button element.
      expect(reExecutionButton.classList.contains('bp5-disabled')).toBe(true);
    });
  });
});
