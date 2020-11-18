import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {WorkspaceContext, WorkspaceProvider} from 'src/workspace/WorkspaceContext';

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
    <MemoryRouter initialEntries={['/workspace/foo@bar/etc']}>
      <ApolloTestProvider mocks={mocks}>
        <WorkspaceProvider>
          <Display />
        </WorkspaceProvider>
      </ApolloTestProvider>
    </MemoryRouter>
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

      render(<Test mocks={mocks} />);

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
  });
});
