import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ApolloTestProvider} from '../testing/ApolloTestProvider';
import {useRepositoryOptions, WorkspaceProvider} from '../workspace/WorkspaceContext';

import {RepositoryPicker} from './RepositoryPicker';

describe('RepositoryPicker', () => {
  const defaultMocks = {
    RepositoryLocationOrLoadFailure: () => ({
      __typename: 'RepositoryLocation',
    }),
    RepositoryLocationsOrError: () => ({
      __typename: 'RepositoryLocationConnection',
    }),
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(1),
    }),
    RepositoryLocation: () => ({
      isReloadSupported: true,
      name: () => 'undisclosed-location',
      repositories: () => new MockList(1),
    }),
  };

  const Test: React.FC = () => {
    const {loading, options} = useRepositoryOptions();
    return (
      <RepositoryPicker
        loading={loading}
        options={options}
        selected={options}
        toggleRepo={() => {}}
      />
    );
  };

  const Wrapper: React.FC<{mocks: any}> = (props) => {
    const {mocks} = props;
    return (
      <MemoryRouter>
        <ApolloTestProvider mocks={mocks}>
          <WorkspaceProvider>
            <Test />
          </WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    );
  };

  it('renders the current repository and refresh button', async () => {
    const mocks = {
      ...defaultMocks,
      Repository: () => ({
        name: () => 'foo-bar',
      }),
    };

    render(<Wrapper mocks={mocks} />);

    await waitFor(() => {
      expect(screen.getByText(/foo-bar/i)).toBeVisible();
      expect(screen.getByRole('button', {name: /refresh/i})).toBeVisible();
    });
  });
});
