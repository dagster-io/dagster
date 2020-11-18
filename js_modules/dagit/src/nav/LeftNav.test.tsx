import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {LeftNav} from 'src/nav/LeftNav';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {WorkspaceProvider} from 'src/workspace/WorkspaceContext';

describe('LeftNav', () => {
  const defaultMocks = {
    RepositoryLocationsOrError: () => ({
      __typename: 'RepositoryLocationConnection',
    }),
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(2),
    }),
    RepositoryLocationOrLoadFailure: () => ({
      __typename: 'RepositoryLocation',
    }),
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <MemoryRouter>
        <ApolloTestProvider mocks={mocks}>
          <WorkspaceProvider>
            <LeftNav />
          </WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    );
  };

  describe('Repo location errors', () => {
    it('shows no errors when there are none', async () => {
      render(<Test mocks={defaultMocks} />);
      await waitFor(() => {
        expect(screen.queryByText(/an error occurred while loading a repository/i)).toBeNull();
      });
    });

    it('shows the error message when repo location errors are found', async () => {
      const mocks = {
        ...defaultMocks,
        RepositoryLocationOrLoadFailure: () => ({
          __typename: 'RepositoryLocationLoadFailure',
        }),
      };

      render(<Test mocks={mocks} />);
      await waitFor(() => {
        expect(screen.getByText(/an error occurred while loading a repository/i)).toBeVisible();
        expect(screen.getByRole('link', {name: /view details/i})).toBeVisible();
      });
    });
  });
});
