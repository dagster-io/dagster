import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {LAST_REPO_KEY, WorkspaceContext, WorkspaceProvider} from 'src/workspace/WorkspaceContext';

describe('WorkspaceContext', () => {
  const Display = () => {
    const {activeRepo, refetch} = React.useContext(WorkspaceContext);
    return (
      <>
        <div>Pipeline count: {activeRepo?.repo.repository.pipelines.length}</div>
        <button onClick={() => refetch()}>Refetch</button>
      </>
    );
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => (
    <ApolloTestProvider mocks={mocks}>
      <WorkspaceProvider>
        <Display />
      </WorkspaceProvider>
    </ApolloTestProvider>
  );

  describe('Repository options', () => {
    const defaultMocks = {
      RepositoryLocationsOrError: () => ({
        __typename: 'RepositoryLocationConnection',
      }),
      RepositoryLocationOrLoadFailure: () => ({
        __typename: 'RepositoryLocation',
      }),
      RepositoryLocation: () => ({
        repositories: () => new MockList(1),
      }),
    };

    it('updates the "current repository" state correctly on refetch', async () => {
      let numPipelines = 1;
      const mocks = {
        ...defaultMocks,
        Repository: () => ({
          pipelines: () => new MockList(numPipelines),
        }),
      };

      render(
        <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
          <Test mocks={mocks} />
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
      });

      numPipelines++;
      userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 2/i)).toBeVisible();
      });

      numPipelines--;
      userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
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

      it('initializes from the first repo option, if no localStorage', async () => {
        render(
          <MemoryRouter initialEntries={['/instance/runs']}>
            <Test mocks={mocks} />
          </MemoryRouter>,
        );

        // Initialize to `lorem@ipsum`, which has two pipelines.
        await waitFor(() => {
          expect(screen.getByText(/pipeline count: 2/i)).toBeVisible();
          expect(window.localStorage.getItem(LAST_REPO_KEY)).toBe('lorem:ipsum');
        });
      });

      it('correctly initializes from localStorage', async () => {
        window.localStorage.setItem(LAST_REPO_KEY, 'foo:bar');
        render(
          <MemoryRouter initialEntries={['/instance/runs']}>
            <Test mocks={mocks} />
          </MemoryRouter>,
        );

        // Initialize to `foo@bar`, which has four pipelines.
        await waitFor(() => {
          expect(screen.getByText(/pipeline count: 4/i)).toBeVisible();
        });
      });
    });
  });
});
