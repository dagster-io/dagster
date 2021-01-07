import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {RepositoryPicker} from 'src/nav/RepositoryPicker';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {useRepositoryOptions, WorkspaceProvider} from 'src/workspace/WorkspaceContext';

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
    return <RepositoryPicker loading={loading} options={options} repo={options[0]} />;
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
