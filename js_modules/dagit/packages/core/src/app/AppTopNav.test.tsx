import {act, render, screen, waitFor, within} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {InstigationStatus} from '../types/globalTypes';

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
        <AppTopNav searchPlaceholder="Test..." rightOfSearchBar={<div>RightOfSearchBar</div>} />
      </TestProvider>,
    );

    await waitFor(() => {
      const runsLink = screen.getByRole('link', {name: /runs/i});
      expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
      expect(screen.getByText('Status').closest('a')).toHaveAttribute('href', '/instance');
      expect(screen.getByText('RightOfSearchBar')).toBeVisible();
    });
  });

  describe('Repo location errors', () => {
    it('does not show warning icon when no errors', async () => {
      await act(async () => {
        render(
          <TestProvider apolloProps={{mocks: [defaultMocks]}}>
            <AppTopNav searchPlaceholder="Test..." />
          </TestProvider>,
        );
      });

      expect(screen.getByText(/workspace/i)).toBeVisible();
      expect(
        screen.queryByRole('img', {
          name: /warning/i,
        }),
      ).toBeNull();
    });

    it('shows the error message when repo location errors are found', async () => {
      const mocks = {
        RepositoryLocationOrLoadError: () => ({
          __typename: 'PythonError',
        }),
      };

      await act(async () => {
        render(
          <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
            <AppTopNav searchPlaceholder="Test..." />
          </TestProvider>,
        );
      });

      expect(screen.getByText(/workspace/i)).toBeVisible();
      expect(
        screen.getByRole('img', {
          name: /warning/i,
        }),
      ).toBeVisible();
    });
  });

  describe('Daemon status errors', () => {
    const mocksWithDaemonError = {
      DaemonHealth: () => ({
        allDaemonStatuses: () => [...new Array(1)],
      }),
      DaemonStatus: () => ({
        id: 'SENSOR',
        daemonType: 'SENSOR',
        required: true,
        healthy: false,
      }),
    };

    const mocksWithSensor = {
      Repository: () => ({
        sensors: () => [...new Array(1)],
      }),
      InstigationState: () => ({
        status: () => InstigationStatus.RUNNING,
      }),
    };

    it('does not show status warning icon if there are sensor daemon errors but no sensors', async () => {
      const mocksWithoutSensor = {
        Repository: () => ({
          sensors: () => [],
        }),
      };

      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocksWithDaemonError, mocksWithoutSensor]}}
          >
            <AppTopNav searchPlaceholder="Test..." showStatusWarningIcon={false} />
          </TestProvider>,
        );
      });

      expect(screen.getByText(/workspace/i)).toBeVisible();
      const link = screen.getByRole('link', {name: /status/i});
      expect(within(link).queryByText(/warning/i)).toBeNull();
    });

    it('shows status warning icon by default, if there are errors', async () => {
      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocksWithDaemonError, mocksWithSensor]}}
          >
            <AppTopNav searchPlaceholder="Test..." />
          </TestProvider>,
        );
      });

      const link = screen.getByRole('link', {
        name: /status warning/i,
      });

      expect(within(link).getByText(/status/i)).toBeVisible();
    });

    it('does not show status warning icon if `showStatusWarningIcon` is false, even with errors', async () => {
      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocksWithDaemonError, mocksWithSensor]}}
          >
            <AppTopNav searchPlaceholder="Test..." showStatusWarningIcon={false} />
          </TestProvider>,
        );
      });

      expect(screen.getByText(/workspace/i)).toBeVisible();
      const link = screen.getByRole('link', {name: /status/i});
      expect(within(link).queryByText(/warning/i)).toBeNull();
    });
  });
});
