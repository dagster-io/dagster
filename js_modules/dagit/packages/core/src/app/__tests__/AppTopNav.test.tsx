import {act, render, screen, waitFor, within} from '@testing-library/react';
import * as React from 'react';

import {InstigationStatus} from '../../graphql/types';
import {
  DeploymentStatusProvider,
  DeploymentStatusType,
} from '../../instance/DeploymentStatusProvider';
import {TestProvider} from '../../testing/TestProvider';
import {AppTopNav} from '../AppTopNav';

// We don't need to render the search input here.
jest.mock('../../search/SearchDialog', () => ({
  SearchDialog: () => <div />,
}));

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
      id: () => 'my_workspace',
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
    Instance: () => ({
      autoMaterializePaused: () => false,
    }),
  };

  const Test: React.FC<{statusPolling?: Set<DeploymentStatusType>; children: React.ReactNode}> = ({
    children,
    statusPolling = new Set(['code-locations', 'daemons']),
  }) => {
    return <DeploymentStatusProvider include={statusPolling}>{children}</DeploymentStatusProvider>;
  };

  it('renders top nav without error', async () => {
    render(
      <TestProvider
        apolloProps={{mocks: [defaultMocks]}}
        routerProps={{initialEntries: ['/locations/my_repository@my_location']}}
      >
        <Test>
          <AppTopNav searchPlaceholder="Test..." rightOfSearchBar={<div>RightOfSearchBar</div>} />
        </Test>
      </TestProvider>,
    );

    await waitFor(() => {
      const runsLink = screen.getByRole('link', {name: /runs/i});
      expect(runsLink.closest('a')).toHaveAttribute('href', '/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/assets');
      expect(screen.getByText('Deployment').closest('a')).toHaveAttribute('href', '/locations');
      expect(screen.getByText('RightOfSearchBar')).toBeVisible();
    });
  });

  describe('Repo location errors', () => {
    it('does not show warning icon when no errors', async () => {
      await act(async () => {
        render(
          <TestProvider apolloProps={{mocks: [defaultMocks]}}>
            <Test>
              <AppTopNav searchPlaceholder="Test..." />
            </Test>
          </TestProvider>,
        );
      });

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
            <Test>
              <AppTopNav searchPlaceholder="Test..." />
            </Test>
          </TestProvider>,
        );
      });

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
            <Test>
              <AppTopNav searchPlaceholder="Test..." />
            </Test>
          </TestProvider>,
        );
      });

      const link = screen.getByRole('link', {name: /deployment/i});
      expect(within(link).queryByText(/warning/i)).toBeNull();
    });

    it('shows deployment warning icon by default, if there are errors', async () => {
      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocksWithDaemonError, mocksWithSensor]}}
          >
            <Test>
              <AppTopNav searchPlaceholder="Test..." />
            </Test>
          </TestProvider>,
        );
      });

      const link = screen.getByRole('link', {
        name: /deployment warning/i,
      });

      expect(within(link).getByText(/deployment/i)).toBeVisible();
    });

    it('does not show deployment warning icon if `statusPolling` does not include `daemons`, even with errors', async () => {
      await act(async () => {
        render(
          <TestProvider
            apolloProps={{mocks: [defaultMocks, mocksWithDaemonError, mocksWithSensor]}}
          >
            <Test statusPolling={new Set(['code-locations'])}>
              <AppTopNav searchPlaceholder="Test..." />
            </Test>
          </TestProvider>,
        );
      });

      const link = screen.getByRole('link', {name: /deployment/i});
      expect(within(link).queryByText(/warning/i)).toBeNull();
    });
  });
});
