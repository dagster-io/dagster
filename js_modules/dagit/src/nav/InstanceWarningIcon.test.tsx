import {MockList} from '@graphql-tools/mock';
import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {InstanceWarningIcon} from 'src/nav/InstanceWarningIcon';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {WorkspaceProvider} from 'src/workspace/WorkspaceContext';

describe('InstanceWarningIcon', () => {
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
    DaemonHealth: () => ({
      allDaemonStatuses: () => new MockList(3),
    }),
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <MemoryRouter>
        <ApolloTestProvider mocks={mocks}>
          <WorkspaceProvider>
            <InstanceWarningIcon />
          </WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    );
  };

  it('displays if any repo errors', async () => {
    const mocks = {
      ...defaultMocks,
      RepositoryLocationOrLoadFailure: () => ({
        __typename: 'RepositoryLocationLoadFailure',
      }),
    };
    render(<Test mocks={mocks} />);
    await waitFor(() => {
      expect(screen.getByText(/warnings found/i)).toBeVisible();
    });
  });

  it('displays if daemon errors', async () => {
    const mocks = {
      ...defaultMocks,
      DaemonStatus: () => ({
        healthy: () => false,
        required: () => true,
      }),
    };

    render(<Test mocks={mocks} />);
    await waitFor(() => {
      expect(screen.getByText(/warnings found/i)).toBeVisible();
    });
  });

  it('does not display if no errors', async () => {
    const mocks = {
      ...defaultMocks,
      DaemonStatus: () => ({
        healthy: () => true,
      }),
    };

    render(<Test mocks={mocks} />);
    await waitFor(() => {
      expect(screen.queryByText(/warnings found/i)).toBeNull();
    });
  });
});
