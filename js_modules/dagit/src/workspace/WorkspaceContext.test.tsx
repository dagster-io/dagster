import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {useWorkspaceState} from 'src/workspace/WorkspaceContext';

describe('WorkspaceContext', () => {
  const Test = () => {
    const {activeRepo} = useWorkspaceState();
    return <div>Pipeline count: {activeRepo?.repo.repository.pipelines.length}</div>;
  };

  describe('Repository options', () => {
    const defaultMocks = {
      RepositoriesOrError: () => ({
        __typename: 'RepositoryConnection',
      }),
      RepositoryConnection: () => ({
        nodes: () => new MockList(1),
      }),
    };

    it('updates the "current repository" state correctly when the repo itself changes', async () => {
      let numPipelines = 1;
      const mocks = {
        ...defaultMocks,
        Repository: () => ({
          pipelines: () => new MockList(numPipelines),
        }),
      };

      const {rerender} = render(
        <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
          <ApolloTestProvider mocks={mocks}>
            <Test key="a" />
          </ApolloTestProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
      });

      numPipelines++;
      rerender(
        <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
          <ApolloTestProvider mocks={mocks}>
            <Test key="b" />
          </ApolloTestProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 2/i)).toBeVisible();
      });

      numPipelines--;
      rerender(
        <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
          <ApolloTestProvider mocks={mocks}>
            <Test key="c" />
          </ApolloTestProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        expect(screen.getByText(/pipeline count: 1/i)).toBeVisible();
      });
    });
  });
});
