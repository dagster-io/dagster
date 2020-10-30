import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {App, AppContent} from 'src/App';
import {breakOnUnderscores} from 'src/Util';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';

describe('App', () => {
  const defaultMocks = {
    Repository: () => ({
      name: () => 'my_repository',
      pipelines: () => new MockList(1),
    }),
    RepositoryOrError: () => ({
      __typename: 'Repository',
    }),
    RepositoriesOrError: () => ({
      __typename: 'RepositoryConnection',
    }),
    RepositoryLocation: () => ({
      name: () => 'my_location',
    }),
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(2),
    }),
    RepositoryLocationsOrError: () => ({
      __typename: 'RepositoryLocationConnection',
      nodes: () => new MockList(2),
    }),
    RepositoryLocationOrLoadFailure: () => ({
      __typename: 'RepositoryLocation',
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
      __typename: () => 'SolidInvocationSite',
      pipeline: () => ({
        __typename: 'Pipeline',
      }),
      solidHandle: () => ({
        handleID: 'foo_handle',
        __typename: 'SolidHandle',
      }),
    }),
    ISolidDefinition: () => ({
      __typename: 'SolidDefinition',
    }),
  };

  it('renders left nav without error', async () => {
    render(
      <ApolloTestProvider mocks={defaultMocks}>
        <App />
      </ApolloTestProvider>,
    );

    const details = await screen.findByText('Instance Details');
    expect(details).toBeVisible();

    const [runsLink] = screen.getAllByText('Runs');
    expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
    expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
    expect(screen.getByText('Scheduler').closest('a')).toHaveAttribute(
      'href',
      '/instance/scheduler',
    );

    expect(screen.getByText('my_repository')).toBeVisible();
  });

  describe('Routes', () => {
    it('renders solid details', async () => {
      render(
        <MemoryRouter initialEntries={['/workspace/my_repository@my_location/solid/foo_solid']}>
          <ApolloTestProvider mocks={defaultMocks}>
            <AppContent />
          </ApolloTestProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', {name: breakOnUnderscores('foo_solid')})).toBeVisible();
        expect(screen.getByText(/inputs/i)).toBeVisible();
        expect(screen.getByText(/outputs/i)).toBeVisible();
        expect(screen.getByText(/all invocations/i)).toBeVisible();
      });
    });

    it('renders solids explorer', async () => {
      render(
        <MemoryRouter initialEntries={['/workspace/my_repository@my_location/solids/foo_solid']}>
          <ApolloTestProvider mocks={defaultMocks}>
            <AppContent />
          </ApolloTestProvider>
        </MemoryRouter>,
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
        ...defaultMocks,
        Pipeline: () => ({
          name: 'foo_pipeline',
        }),
        PipelineSnapshot: () => ({
          runs: () => new MockList(0),
          schedules: () => new MockList(0),
        }),
        PipelineSnapshotOrError: () => ({
          __typename: 'PipelineSnapshot',
        }),
      };

      render(
        <MemoryRouter
          initialEntries={['/workspace/my_repository@my_location/pipelines/foo_pipeline/overview']}
        >
          <ApolloTestProvider mocks={mocks}>
            <AppContent />
          </ApolloTestProvider>
        </MemoryRouter>,
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
