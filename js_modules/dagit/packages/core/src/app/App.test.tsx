import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {App} from './App';
import {breakOnUnderscores} from './Util';

// Import lazy routes up front so that they don't slow down the tests.
import './FeatureFlagsRoot';
import '../instance/InstanceRoot';
import '../workspace/WorkspaceRoot';

describe('App', () => {
  const defaultMocks = {
    Repository: () => ({
      name: () => 'my_repository',
      pipelines: () => new MockList(1),
    }),
    RepositoryLocation: () => ({
      environmentPath: () => 'what then',
      id: () => 'my_location',
      name: () => 'my_location',
      repositories: () => new MockList(1),
    }),
    Workspace: () => ({
      locationEntries: () => new MockList(1),
    }),
    RepositoryOrigin: () => ({
      repositoryName: () => 'my_repository',
      repositoryLocationName: () => 'my_location',
    }),
    SolidDefinition: () => ({
      configField: null,
      description: null,
      inputDefinitions: () => new MockList(1),
      outputDefinitions: () => new MockList(1),
      metadata: () => [],
      name: 'foo_solid',
      requiredResources: () => new MockList(0),
    }),
    SolidInvocationSite: () => ({
      solidHandle: () => ({
        handleID: 'foo_handle',
      }),
    }),
  };

  it('renders left nav without error', async () => {
    render(
      <TestProvider apolloProps={{mocks: defaultMocks}}>
        <App />
      </TestProvider>,
    );

    await waitFor(() => {
      const instanceHeader = screen.getByText(/instance/i);
      expect(instanceHeader).toBeVisible();
      const [runsLink] = screen.getAllByText('Runs');
      expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
      expect(screen.getByText('Status').closest('a')).toHaveAttribute('href', '/instance');
      expect(screen.getByText('my_repository')).toBeVisible();
    });
  });

  describe('Routes', () => {
    it('renders solids explorer', async () => {
      render(
        <TestProvider
          routerProps={{initialEntries: ['/workspace/my_repository@my_location/solids/foo_solid']}}
          apolloProps={{mocks: defaultMocks}}
        >
          <App />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Filter by name or input/output type...')).toBeVisible();
        expect(screen.getByRole('heading', {name: breakOnUnderscores('foo_solid')})).toBeVisible();
        expect(screen.getByText(/inputs/i)).toBeVisible();
        expect(screen.getByText(/outputs/i)).toBeVisible();
        expect(screen.getByText(/all invocations/i)).toBeVisible();
      });
    });

    it('renders pipeline overview', async () => {
      const mocks = {
        Pipeline: () => ({
          name: 'foo_pipeline',
        }),
        PipelineSnapshot: () => ({
          runs: () => new MockList(0),
          schedules: () => new MockList(0),
          sensors: () => new MockList(0),
        }),
      };

      render(
        <TestProvider
          routerProps={{
            initialEntries: [
              '/workspace/my_repository@my_location/pipelines/foo_pipeline/overview',
            ],
          }}
          apolloProps={{mocks: [defaultMocks, mocks]}}
        >
          <App />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByRole('tablist')).toBeVisible();
        expect(screen.getByRole('link', {name: /overview/i})).toBeVisible();
        expect(screen.getByText(/no pipeline schedules/i)).toBeVisible();
        expect(screen.getByText(/no recent assets/i)).toBeVisible();
      });
    });
  });
});
