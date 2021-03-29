import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloTestProvider} from '../testing/ApolloTestProvider';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {LAST_REPO_KEY, LeftNavRepositorySection, REPO_KEYS} from './LeftNavRepositorySection';

describe('Repository options', () => {
  const defaultMocks = {
    RepositoryLocationsOrError: () => ({
      __typename: 'RepositoryLocationConnection',
    }),
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(1),
    }),
    RepositoryLocationOrLoadFailure: () => ({
      __typename: 'RepositoryLocation',
    }),
    RepositoryLocation: () => ({
      name: () => 'bar',
      repositories: () => new MockList(1),
    }),
    SchedulesOrError: () => ({
      __typename: 'Schedules',
    }),
    Schedules: () => ({
      results: () => new MockList(0),
    }),
    SensorsOrError: () => ({
      __typename: 'Sensors',
    }),
    Sensors: () => ({
      results: () => new MockList(0),
    }),
  };

  it('Corrctly displays the current repository state', async () => {
    const mocks = {
      ...defaultMocks,
      Repository: () => ({
        name: () => 'foo',
        pipelines: () => new MockList(1),
      }),
      Pipeline: () => ({
        id: () => 'my_pipeline',
        name: () => 'my_pipeline',
      }),
    };

    render(
      <ApolloTestProvider mocks={mocks}>
        <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
          <WorkspaceProvider>
            <LeftNavRepositorySection />
          </WorkspaceProvider>
        </MemoryRouter>
      </ApolloTestProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole('link', {
          name: /my_pipeline/i,
        }),
      ).toBeVisible();
    });
  });

  describe('localStorage', () => {
    beforeEach(() => {
      window.localStorage.clear();
    });

    const locationOne = 'ipsum';
    const repoOne = 'lorem';
    const locationTwo = 'bar';
    const repoTwo = 'foo';

    const mocks = {
      ...defaultMocks,
      RepositoryLocationConnection: () => ({
        nodes: () => [
          {
            __typename: 'RepositoryLocation',
            name: locationOne,
            repositories: () =>
              new MockList(1, () => ({
                name: repoOne,
                pipelines: () => new MockList(2),
              })),
          },
          {
            __typename: 'RepositoryLocation',
            name: locationTwo,
            repositories: () =>
              new MockList(1, () => ({
                name: repoTwo,
                pipelines: () => new MockList(4),
              })),
          },
        ],
      }),
    };

    it('initializes with first repo option, if no localStorage', async () => {
      render(
        <ApolloTestProvider mocks={mocks}>
          <MemoryRouter initialEntries={['/instance/runs']}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MemoryRouter>
        </ApolloTestProvider>,
      );

      await waitFor(() => {
        // Three links. One for repo, two for pipelines.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes with correct repo option, if `LAST_REPO_KEY` localStorage', async () => {
      window.localStorage.setItem(LAST_REPO_KEY, 'lorem:ipsum');
      render(
        <ApolloTestProvider mocks={mocks}>
          <MemoryRouter initialEntries={['/instance/runs']}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MemoryRouter>
        </ApolloTestProvider>,
      );

      await waitFor(() => {
        // Three links. One for repo, two for pipelines.
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes with correct repo option, if `REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(REPO_KEYS, '["foo:bar"]');
      render(
        <ApolloTestProvider mocks={mocks}>
          <MemoryRouter initialEntries={['/instance/runs']}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MemoryRouter>
        </ApolloTestProvider>,
      );

      // Initialize to `foo@bar`, which has four pipelines. Plus one for repo.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(5);
      });
    });

    it('initializes with first repo option, if no matching `REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(REPO_KEYS, '["hello:world"]');
      render(
        <ApolloTestProvider mocks={mocks}>
          <MemoryRouter initialEntries={['/instance/runs']}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MemoryRouter>
        </ApolloTestProvider>,
      );

      // Initialize to `lorem@ipsum`, which has two pipelines. Plus one for repo.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(3);
      });
    });

    it('initializes with multiple repo option, if multiple `REPO_KEYS` localStorage', async () => {
      window.localStorage.setItem(REPO_KEYS, '["lorem:ipsum", "foo:bar"]');
      render(
        <ApolloTestProvider mocks={mocks}>
          <MemoryRouter initialEntries={['/instance/runs']}>
            <WorkspaceProvider>
              <LeftNavRepositorySection />
            </WorkspaceProvider>
          </MemoryRouter>
        </ApolloTestProvider>,
      );

      // Six total pipelines, and no link for single repo name.
      await waitFor(() => {
        expect(screen.getAllByRole('link')).toHaveLength(6);
      });
    });
  });
});
