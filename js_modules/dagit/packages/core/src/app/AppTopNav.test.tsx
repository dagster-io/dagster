import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {AppTopNav} from './AppTopNav';

describe('AppTopNav', () => {
  const defaultMocks = {
    Repository: () => ({
      name: () => 'my_repository',
      pipelines: () => [...new Array(1)],
    }),
    RepositoryLocation: () => ({
      environmentPath: () => 'what then',
      id: () => 'my_location',
      name: () => 'my_location',
      repositories: () => [...new Array(1)],
    }),
    Workspace: () => ({
      locationEntries: () => [...new Array(1)],
    }),
    RepositoryOrigin: () => ({
      repositoryName: () => 'my_repository',
      repositoryLocationName: () => 'my_location',
    }),
    SolidDefinition: () => ({
      configField: null,
      description: null,
      inputDefinitions: () => [...new Array(1)],
      outputDefinitions: () => [...new Array(1)],
      metadata: () => [],
      name: 'foo_solid',
      requiredResources: () => [],
    }),
    SolidInvocationSite: () => ({
      solidHandle: () => ({
        handleID: 'foo_handle',
      }),
    }),
    DaemonHealth: () => ({
      allDaemonStatuses: () => [],
    }),
  };

  it('renders top nav without error', async () => {
    render(
      <TestProvider
        apolloProps={{mocks: [defaultMocks]}}
        routerProps={{initialEntries: ['/workspace/my_repository@my_location']}}
      >
        <AppTopNav searchPlaceholder="Test..." />
      </TestProvider>,
    );

    await waitFor(() => {
      const runsLink = screen.getByRole('link', {name: /runs/i});
      expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
      expect(screen.getByText('Status').closest('a')).toHaveAttribute('href', '/instance');
    });
  });

  describe('Repo location errors', () => {
    it('does not show warning icon when no errors', async () => {
      render(
        <TestProvider apolloProps={{mocks: [defaultMocks]}}>
          <AppTopNav searchPlaceholder="Test..." />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/workspace/i)).toBeVisible();
        expect(
          screen.queryByRole('img', {
            name: /warning/i,
          }),
        ).toBeNull();
      });
    });

    // todo dish: Figure out what graphql-tools is doing with this mock. 🤪
    it.skip('shows the error message when repo location errors are found', async () => {
      const mocks = {
        RepositoryLocationOrLoadError: () => ({
          __typename: 'PythonError',
        }),
      };

      render(
        <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
          <AppTopNav searchPlaceholder="Test..." />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/workspace/i)).toBeVisible();
        expect(
          screen.getByRole('img', {
            name: /warning/i,
          }),
        ).toBeVisible();
      });
    });
  });
});
